from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict, MutableList
from typing import Optional
from wtforms import HiddenField, SelectMultipleField

from eNMS.database import CustomMediumBlobPickle, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.services import DictValidationForm, NapalmForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class NapalmGettersService(Service):

    __tablename__ = "NapalmGettersService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    validation_method = Column(String(SMALL_STRING_LENGTH), default="dict_included")
    dict_match = Column(MutableDict.as_mutable(CustomMediumBlobPickle), default={})
    driver = Column(String(SMALL_STRING_LENGTH), default="")
    use_device_driver = Column(Boolean, default=True)
    getters = Column(MutableList.as_mutable(PickleType), default=[])
    negative_logic = Column(Boolean, default=False)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {"polymorphic_identity": "NapalmGettersService"}

    def job(self, payload: dict, device: Device, parent: Optional[Job] = None) -> dict:
        napalm_connection, result = self.napalm_connection(device, parent), {}
        self.log(
            parent,
            "info",
            f"Fetching NAPALM getters ({', '.join(self.getters)}) on {device.name}",
        )
        for getter in self.getters:
            try:
                result[getter] = getattr(napalm_connection, getter)()
            except Exception as e:
                result[getter] = f"{getter} failed because of {e}"
        match = (
            self.sub(self.content_match, locals())
            if self.validation_method == "text"
            else self.sub(self.dict_match, locals())
        )
        return {
            "match": match,
            "negative_logic": self.negative_logic,
            "result": result,
            "success": self.match_content(result, match),
        }


class NapalmGettersForm(ServiceForm, NapalmForm, DictValidationForm):
    form_type = HiddenField(default="NapalmGettersService")
    getters = SelectMultipleField(
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
