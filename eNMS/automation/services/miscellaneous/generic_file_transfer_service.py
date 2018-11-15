# This class serves as a template example for the user to understand
# how to implement their own custom services to eNMS.
# It can be removed if you are deploying eNMS in production.

# Each new service must inherit from the "Service" class.
# eNMS will automatically generate a form in the web GUI by looking at the
# SQL parameters of the class.
# By default, a property (String, Float, Integer) will be displayed in the GUI
# with a text area for the input.
# If the property in a Boolean, it will be displayed as a tick box instead.
# If the class contains a "property_name_values" property with a list of
# values, it will be displayed:
# - as a multiple selection list if the property is an SQL "MutableList".
# - as a single selection drop-down list in all other cases.
# If you want to see a few examples of services, you can have a look at the
# /netmiko, /napalm and /miscellaneous subfolders in /eNMS/eNMS/services.

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

import os
import paramiko
from scp import SCPClient
from logging import error

class GenericFileTransferService(Service):

    __tablename__ = 'GenericFileTransferService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    # see eNMS documentation section on Workflow devices for a description of
    # the multiprocessing property and its expected behavior
    multiprocessing = True

    filetransfer_direction = Column(String)
    filetransfer_direction_values = (('get', 'Get'), ('put', 'Put'))
    filetransfer_type = Column(String)
    filetransfer_type_values = (('scp', 'SCP'), ('sftp', 'SFTP'))

    source_file = Column(String)
    destination_file = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'GenericFileTransferService',
    }

    def job(self, device, payload):
        # The "job" function is called when the service is executed.
        # The parameters of the service can be accessed with self (self.string1,
        # self.boolean1, etc)
        # You can look at how default services (netmiko, napalm, etc.) are
        # implemented in the /services subfolders (/netmiko, /napalm, etc).
        # "results" is a dictionnary that will be displayed in the logs.
        # It must contain at least a key "success" that indicates whether
        # the execution of the service was a success or a failure.
        # In a workflow, the "success" value will determine whether to move
        # forward with a "Success" edge or a "Failure" edge.
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
            #error(f"{device.ip_address}{device.username}{device.password}")
            ssh.connect(device.ip_address, username=device.username, password=device.password, look_for_keys=False)
            if self.filetransfer_type == 'sftp':
                sftp = ssh.open_sftp()
                if self.filetransfer_direction == 'put':
                    sftp.put(self.source_file, self.destination_file)
                else: # get:
                    sftp.get(self.source_file, self.destination_file)
                sftp.close()
            else: # scp:
                with SCPClient(ssh.get_transport()) as scp:
                    if self.filetransfer_direction == 'put':
                        scp.put(self.source_file, self.destination_file)
                    else: # get:
                        scp.get(self.source_file, self.destination_file)
            ssh.close()
        except Exception as e:
            return {'success': False, 'result': str(e)}
        return {'success': True, 'result': 'File %s transferred successfully' % self.source_file}


service_classes['GenericFileTransferService'] = GenericFileTransferService