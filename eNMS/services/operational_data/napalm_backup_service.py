from datetime import datetime
from flask_wtf import FlaskForm
from pathlib import Path
from re import M, sub
from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms import HiddenField, StringField, SelectMultipleField, FieldList, FormField


from eNMS.database.dialect import Column, MutableList, SmallString, MutableDict
from eNMS.forms.automation import NapalmForm
from eNMS.models.automation import ConnectionService


class NapalmBackupService(ConnectionService):

    __tablename__ = "napalm_backup_service"
    pretty_name = "NAPALM Operational Data Backup"
    parent_type = "connection_service"
    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    timeout = Column(Integer, default=60)
    optional_args = Column(MutableDict)
    configuration = Column(MutableList)
    operational_data = Column(MutableList)
    replacements = Column(MutableList)

    __mapper_args__ = {"polymorphic_identity": "napalm_backup_service"}

    def job(self, run, payload, device):
        path = Path.cwd() / "network_data" / device.name
        path.mkdir(parents=True, exist_ok=True)
        try:
            device.last_runtime = datetime.now()
            napalm_connection = run.napalm_connection(device)
            run.log("info", "Fetching Operational Data", device)
            for data_type in ("configuration", "operational_data"):
                for getter in getattr(run, data_type):
                    try:
                        result = getattr(napalm_connection, getter)()
                        for r in self.replacements:
                            result = sub(
                                r["pattern"],
                                r["replace_with"],
                                str(result),
                                flags=M,
                            )
                    except Exception as e:
                        result = f"{getter} failed because of {e}"
                setattr(device, data_type, result)
                with open(path / data_type, "w") as file:
                    file.write(str(result))
            device.last_status = "Success"
            device.last_duration = (
                f"{(datetime.now() - device.last_runtime).total_seconds()}s"
            )
            device.last_update = str(device.last_runtime)
            run.generate_yaml_file(path, device)
        except Exception as e:
            device.last_status = "Failure"
            device.last_failure = str(device.last_runtime)
            run.generate_yaml_file(path, device)
            return {"success": False, "result": str(e)}
        return {"success": True}


class ReplacementForm(FlaskForm):
    pattern = StringField("Pattern")
    replace_with = StringField("Replace With")


class NapalmBackupForm(NapalmForm):
    form_type = HiddenField(default="napalm_backup_service")
    configuration = SelectMultipleField(
        choices=(
            ("get_arp_table", "ARP table"),
            ("get_interfaces_counters", "Interfaces counters"),
            ("get_facts", "Facts"),
            ("get_environment", "Environment"),
            ("get_config", "Configuration"),
            ("get_interfaces", "Interfaces"),
            ("get_interfaces_ip", "Interface IP"),
            ("get_lldp_neighbors", "LLDP neighbors"),
            ("get_lldp_neighbors_detail", "LLDP neighbors detail"),
            ("get_mac_address_table", "MAC address"),
            ("get_ntp_servers", "NTP servers"),
            ("get_ntp_stats", "NTP statistics"),
            ("get_optics", "Transceivers"),
            ("get_snmp_information", "SNMP"),
            ("get_users", "Users"),
            ("get_network_instances", "Network instances (VRF)"),
            ("get_ntp_peers", "NTP peers"),
            ("get_bgp_config", "BGP configuration"),
            ("get_bgp_neighbors", "BGP neighbors"),
            ("get_ipv6_neighbors_table", "IPv6"),
            ("is_alive", "Is alive"),
        )
    )
    operational_data = SelectMultipleField(
        choices=(
            ("get_arp_table", "ARP table"),
            ("get_interfaces_counters", "Interfaces counters"),
            ("get_facts", "Facts"),
            ("get_environment", "Environment"),
            ("get_config", "Configuration"),
            ("get_interfaces", "Interfaces"),
            ("get_interfaces_ip", "Interface IP"),
            ("get_lldp_neighbors", "LLDP neighbors"),
            ("get_lldp_neighbors_detail", "LLDP neighbors detail"),
            ("get_mac_address_table", "MAC address"),
            ("get_ntp_servers", "NTP servers"),
            ("get_ntp_stats", "NTP statistics"),
            ("get_optics", "Transceivers"),
            ("get_snmp_information", "SNMP"),
            ("get_users", "Users"),
            ("get_network_instances", "Network instances (VRF)"),
            ("get_ntp_peers", "NTP peers"),
            ("get_bgp_config", "BGP configuration"),
            ("get_bgp_neighbors", "BGP neighbors"),
            ("get_ipv6_neighbors_table", "IPv6"),
            ("is_alive", "Is alive"),
        )
    )
    replacements = FieldList(FormField(ReplacementForm), min_entries=3)
    groups = {
        "Create Configuration File": {
            "commands": ["configuration"],
            "default": "expanded",
        },
        "Create Operational Data File": {
            "commands": ["operational_data"],
            "default": "expanded",
        },
        "Search Response & Replace": {
            "commands": ["replacements"],
            "default": "expanded",
        },
        **NapalmForm.groups,
    }
