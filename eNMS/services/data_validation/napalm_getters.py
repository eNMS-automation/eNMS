from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms import HiddenField, SelectMultipleField

from eNMS.database.dialect import Column, MutableDict, MutableList, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.services import DictValidationForm, NapalmForm
from eNMS.models.automation import ConnectionService


class NapalmGettersService(ConnectionService):

    __tablename__ = "napalm_getters_service"

    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    has_targets = True
    validation_method = Column(SmallString, default="dict_included")
    dict_match = Column(MutableDict)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    getters = Column(MutableList)
    negative_logic = Column(Boolean, default=False)
    optional_args = Column(MutableDict)

    __mapper_args__ = {"polymorphic_identity": "napalm_getters_service"}

    def job(self, run, payload, device):
        napalm_connection, result = run.napalm_connection(device), {}
        run.log(
            "info",
            f"Fetching NAPALM getters ({', '.join(run.getters)}) on {device.name}",
        )
        for getter in run.getters:
            try:
                result[getter] = getattr(napalm_connection, getter)()
            except Exception as e:
                result[getter] = f"{getter} failed because of {e}"
        match = (
            run.sub(run.content_match, locals())
            if run.validation_method == "text"
            else run.sub(run.dict_match, locals())
        )
        return {
            "match": match,
            "negative_logic": run.negative_logic,
            "result": result,
            "success": run.match_content(result, match),
        }


class NapalmGettersForm(ServiceForm, NapalmForm, DictValidationForm):
    form_type = HiddenField(default="napalm_getters_service")
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
