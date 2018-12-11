"""Device Upgrade Custom Service"""
##############################################################################
#
# device_upgrade.py
#
# Custom Service for devices that require complex custom logic to complete
# the upgrade process. This service receives payload data from previously
# run services in the workflow, and it generates an additional dictionary
# structured result set that is added to the workflow payload.
#
# Original, shorton, 102918
##############################################################################

# Importing SQL Alchemy column types to handle all of the types of
# form additions that the user could have.
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    PickleType,
    String
)

from sqlalchemy.ext.mutable import MutableDict, MutableList

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes

from eNMS.automation.helpers import (
    netmiko_connection,
    NETMIKO_DRIVERS,
    napalm_connection,
    NAPALM_DRIVERS,
    substitute
)

from logging import error

import time


class DeviceUpgradeService(Service):
    __tablename__ = 'DeviceUpgradeService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    upgrade_from = Column(String)
    upgrade_to = Column(String)
    upgrade_file = Column(String)

    has_targets = True

    __mapper_args__ = {
        'polymorphic_identity': 'DeviceUpgradeService',
    }

    def ciena6500_upgrade_device(self, device, payload):
        success, result = True, {}

        netmiko_handler = netmiko_connection(self, device)
        if self.upgrade_from is None or self.upgrade_to is None or self.upgrade_file is not None:
            # Don't continue if the input fields are not provided
            error('Missing input field.')
            return {'success': False, 'result': {'Input Field Validation': 'Missing input field'}}

        # Check the payload from previous jobs for this device to validate that we are
        # good-to-go to perform the upgrade
        preCheckData = payload["Ciena6500_Pre_Check"]["result"]["devices"][device.name]["result"]["get_facts"]

        # Check the current software version.
        found_sw_version = preCheckData["os_version"]
        for shelf in found_sw_version:
            if found_sw_version[shelf]!=self.upgrade_from:
                return {'success': False, 'result': {'NE is at the wrong initial release': {"Expected": self.upgrade_from, "Found": found_sw_version}}}
            elif found_sw_version[shelf]==self.upgrade_to:
                return {'success': False, 'result': {'NE has already been upgraded to the target release.': {"Expected": self.upgrade_from, "Found": found_sw_version}}}

        # Make sure that the upgrade software has been delivered to the NE.
        for shelf in preCheckData["available_releases"]:
            if preCheckData["available_releases"][shelf].get(self.upgrade_to)==None:
                return {'success': False, 'result': {"Upgrade software has not been delivered to the NE.": {"Expected": self.upgrade_to, "Found": preCheckData["available_releases"]}}}

        # Check the current upgrade state to ensure that an upgrade is not already in progress.
        shelf_upgrade_state=preCheckData["shelf_upgrade_state"]
        for shelf in shelf_upgrade_state:
            if shelf_upgrade_state[shelf]["UPGRDSTAGE"]!="INACTIVE":
                return {'success': False, 'result': {"An upgrade is already in progress.": {"Found": shelf_upgrade_state}}}

        # Start of the upgrade process state machine
        # Four steps: LOAD, 1ST INVOKE, 2ND INVOKE, COMMIT
        # If the upgrade fails before the commital, the entire upgrade will be
        # cancelled and backed out.

        # LOAD
        command="LOAD-UPGRD:::T2::%s:ALRMS=N;" % (self.upgrade_to)
        output=netmiko_handler.send_command(command)

        while True:
            time.sleep(60)
            upgState=self.getUpgradeState(device)
            if upgState=={}:
                return {'success': False, 'result': {"Unexpected Upgrade State": {"Found": upgState}}}
            breakout=True
            for shelf in upgState:
                if upgState[shelf]["UPGRDRSLT"]=="INPROGRESS":
                    breakout=False
            if breakout:
                break
        for shelf in upgState:
            if upgState[shelf]["UPGRDSTAGE"]=="LOAD" and upgState[shelf]["UPGRDRSLT"]=="FAIL":
                output=netmiko_handler.send_command("CANC-UPGRD:::T2;")
                return {'success': False, 'result': {"The Load step failed on a shelf.": {"Found": upgState}}}
            elif upgState[shelf]["UPGRDSTAGE"]=="INACTIVE":
                output=netmiko_handler.send_command("CANC-UPGRD:::T2;")
                return {'success': False, 'result': {"The Check step failed on a shelf.": {"Found": upgState}}}
            elif upgState[shelf]["UPGRDSTAGE"]=="LOAD" and upgState[shelf]["UPGRDRSLT"]=="PASS":
                continue
            else:
                output=netmiko_handler.send_command("CANC-UPGRD:::T2;")
                return {'success': False, 'result': {"Unexpected Upgrade State": {"Found": upgState}}}

        # 1ST INVOKE
        command="INVK-UPGRD:::T2;"
        output=netmiko_handler.send_command(command)

        reconnectAttempt=0
        while True:
            try:
                if not(netmiko_handler and netmiko_handler.is_active()):
                    if reconnectAttempt<3:
                        netmiko_handler = netmiko_connection(self, device)
                        reconnectAttempt+=1
                    else:
                        return {'success': False, 'result': {"Unable to reconnect after the 1st Invoke": {"Attempts made": reconnectAttempt}}}
                time.sleep(60)
                # Per Ciena's upgrade MOP, we must check and wait for all "Member Release
                # Misaligned”, “Member Shelf Unreachable” and "Redundant Release Synch in
                # Progress" alarms to clear before continuing.
                while True:
                    napalm_driver = napalm_connection(self, device)
                    napalm_driver.open()
                    napalm_getter = "get_facts"
                    alarmList=getattr(napalm_driver, napalm_getter)()["alarm_list"]
                    napalm_driver.close()
                    breakout=True
                    for alarm in alarmList:
                        if alarm["CONDDESCR"]=="Member Release Misaligned" or alarm["CONDDESCR"]=="Member Shelf Unreachable" or alarm["CONDDESCR"]=="Redundant Release Synch in Progress":
                            breakout=False
                            time.sleep(60)
                    if breakout:
                        break
                upgState=self.getUpgradeState(device)
                if upgState=={}:
                    return {'success': False, 'result': {"Unexpected Upgrade State": {"Found": upgState}}}
                breakout=True
                for shelf in upgState:
                    if upgState[shelf]["UPGRDRSLT"]=="INPROGRESS":
                        breakout=False
                if breakout:
                    break
            except (OSError, TimeoutError):
                if reconnectAttempt<3:
                    time.sleep(60)
                    netmiko_handler = netmiko_connection(self, device)
                    reconnectAttempt+=1
                else:
                    return {'success': False, 'result': {"Unable to reconnect after the 1st Invoke": {"Attempts made": reconnectAttempt}}}
            except Exception as e:
                return {'success': False, 'result': {"Unexpected error": {"Error": e}}}
        for shelf in upgState:
            if upgState[shelf]["UPGRDSTAGE"]=="1ST_INVOKE" and upgState[shelf]["UPGRDRSLT"]=="FAIL":
                output=netmiko_handler.send_command("CANC-UPGRD:::T2;")
                return {'success': False, 'result': {"The 1st Invoke step failed on a shelf.": {"Found": upgState}}}
            elif upgState[shelf]["UPGRDSTAGE"]=="1ST_INVOKE" and upgState[shelf]["UPGRDRSLT"]=="PASS":
                continue
            else:
                output=netmiko_handler.send_command("CANC-UPGRD:::T2;")
                return {'success': False, 'result': {"Unexpected Upgrade State": {"Found": upgState}}}

        # 2ND INVOKE
        command="INVK-UPGRD:::T2:::AUTOMATIC=N;"
        output=netmiko_handler.send_command(command)

        while True:
            time.sleep(60)
            upgState=self.getUpgradeState(device)
            breakout=True
            for shelf in upgState:
                if upgState[shelf]["UPGRDRSLT"]=="INPROGRESS":
                    breakout=False
            if breakout:
                break
        for shelf in upgState:
            if upgState[shelf]["UPGRDSTAGE"]=="2ND_INVOKE" and upgState[shelf]["UPGRDRSLT"]=="FAIL":
                self.runTL1("CANC-UPGRD:::T2;")
                return {'success': False, 'result': {"Failed the 2nd Invoke": {"Found": upgState}}}
            elif upgState[shelf]["UPGRDSTAGE"]=="2ND_INVOKE" and upgState[shelf]["UPGRDRSLT"]=="PASS":
                continue
            else:
                output=netmiko_handler.send_command("CANC-UPGRD:::T2;")
                return {'success': False, 'result': {"Unexpected Upgrade State": {"Found": upgState}}}

        # COMMIT
        command="CMMT-UPGRD:::T2;"
        output=netmiko_handler.send_command(command)

        while True:
            time.sleep(60)
            upgState=self.getUpgradeState(device)
            breakout=True
            for shelf in upgState:
                if upgState[shelf]["UPGRDRSLT"]=="INPROGRESS":
                    breakout=False
            if breakout:
                break
        for shelf in upgState:
            if upgState[shelf]["UPGRDSTAGE"]=="COMMIT" and upgState[shelf]["UPGRDRSLT"]=="FAIL":
                self.runTL1("CANC-UPGRD:::T2;")
                return {'success': False, 'result': {"Failed the Commit": {"Found": upgState}}}
            elif upgState[shelf]["UPGRDSTAGE"]=="COMMIT" and upgState[shelf]["UPGRDRSLT"]=="PASS":
                continue
            elif upgState[shelf]["UPGRDSTAGE"]=="INACTIVE":
                continue
            else:
                output=netmiko_handler.send_command("CANC-UPGRD:::T2;")
                return {'success': False, 'result': {"Unexpected Upgrade State": {"Found": upgState}}}

        # Upgrade is complete. Perform post upgrade checks and clean up.

        # Delete the initial software release.
        command="DLT-RELEASE:::T2::%s:MINIMAL=N;" % (self.upgrade_from)
        output=netmiko_handler.send_command(command)

        time.sleep(60)

        # Run a post upgrade get_facts
        try:
            napalm_driver=napalm_connection(self, device)
            napalm_driver.open()
            napalm_getter="get_facts"
            postCheckData=getattr(napalm_driver, napalm_getter)()
            napalm_driver.close()
        except:
            return {'success': False, 'result': {'Unable to run post upgrade check.'}}

        # Check that the active software version reports as the upgrade release
        for shelf in currentRel:
            if postCheckData["os_version"][shelf]!=self.upgrade_to:
                return {'success': False, 'result': {'NE at the wrong terminal release': {"Expected": self.upgrade_to, "Found": currentRel}}}
            elif postCheckData["os_version"][shelf]==self.upgrade_to:
                continue

        # Check that the initial software release was deleted from each shelf.
        for shelf in postCheckData["available_releases"]:
            if postCheckData["available_releases"][shelf].get(self.upgrade_from)!=None:
                return {'success': False, 'result': {"Initial release could not be deleted from the NE.": {"Found": postCheckData["available_releases"]}}}

        # If we reach this point, the upgrade is complete and successful.
        # If there is a traffic outage, manual intervention by the NOC
        # would be required. Once committed, there is no rollback option.
        return {'success': success, 'result': result}

    def getUpgradeState(self, device):
        try:
            napalm_driver = napalm_connection(self, device)
            napalm_driver.open()
            napalm_getter = "get_facts"
            upgradeState=getattr(napalm_driver, napalm_getter)()["shelf_upgrade_state"]
            napalm_driver.close()
        except:
            upgradeState={}

        return upgradeState

service_classes['DeviceUpgradeService'] = DeviceUpgradeService