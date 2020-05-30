from datetime import datetime
from flask_wtf import FlaskForm
from pathlib import Path
from re import M, sub
from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms import FormField

from eNMS import app
from eNMS.database import db
from eNMS.forms.automation import NapalmForm
from eNMS.forms.fields import HiddenField, StringField, SelectMultipleField, FieldList
from eNMS.models.automation import ConnectionService


class NapalmBackupService(ConnectionService):

    __tablename__ = "napalm_backup_service"
    pretty_name = "NAPALM Operational Data Backup"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    driver = db.Column(db.SmallString)
    use_device_driver = db.Column(Boolean, default=True)
    timeout = db.Column(Integer, default=60)
    optional_args = db.Column(db.Dict)
    configuration_getters = db.Column(db.List)
    operational_data_getters = db.Column(db.List)
    replacements = db.Column(db.List)

    __mapper_args__ = {"polymorphic_identity": "napalm_backup_service"}

    def job(self, run, payload, device):
        path = Path.cwd() / "network_data" / device.name
        path.mkdir(parents=True, exist_ok=True)
        try:
            device.last_runtime = datetime.now()
            napalm_connection = run.napalm_connection(device)
            run.log("info", "Fetching Operational Data", device)
            for data_type in ("configuration_getters", "operational_data_getters"):
                result = {}
                for getter in getattr(run, data_type):
                    try:
                        output = app.str_dict(getattr(napalm_connection, getter)())
                        for r in self.replacements:
                            output = sub(
                                r["pattern"], r["replace_with"], output, flags=M,
                            )
                        result[getter] = output
                    except Exception as exc:
                        result[getter] = f"{getter} failed because of {exc}"
                if not result:
                    continue
                result = app.str_dict(result)
                setattr(device, data_type, result)
                with open(path / data_type, "w") as file:
                    file.write(result)
            device.last_status = "Success"
            device.last_duration = (
                f"{(datetime.now() - device.last_runtime).total_seconds()}s"
            )
            device.last_update = str(device.last_runtime)
            run.generate_yaml_file(path, device)
        except Exception as exc:
            device.last_status = "Failure"
            device.last_failure = str(device.last_runtime)
            run.generate_yaml_file(path, device)
            return {"success": False, "result": str(exc)}
        return {"success": True}


class ReplacementForm(FlaskForm):
    pattern = StringField("Pattern")
    replace_with = StringField("Replace With")


class NapalmBackupForm(NapalmForm):
    form_type = HiddenField(default="napalm_backup_service")
    configuration_getters = SelectMultipleField(
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
    operational_data_getters = SelectMultipleField(
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
            "commands": ["configuration_getters"],
            "default": "expanded",
        },
        "Create Operational Data File": {
            "commands": ["operational_data_getters"],
            "default": "expanded",
        },
        "Search Response & Replace": {
            "commands": ["replacements"],
            "default": "expanded",
        },
        **NapalmForm.groups,
    }
