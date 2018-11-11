from re import search
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict, MutableList

from eNMS.automation.helpers import (
    napalm_connection,
    NAPALM_DRIVERS,
    substitute
)
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class NapalmGettersService(Service):

    __tablename__ = 'NapalmGettersService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    multiprocessing = True
    content_match = Column(String)
    content_match_regex = Column(Boolean)
    driver = Column(String)
    driver_values = NAPALM_DRIVERS
    getters = Column(MutableList.as_mutable(PickleType), default=[])
    getters_values = (
        ('get_arp_table', 'ARP table'),
        ('get_interfaces_counters', 'Interfaces counters'),
        ('get_facts', 'Facts'),
        ('get_environment', 'Environment'),
        ('get_config', 'Configuration'),
        ('get_interfaces', 'Interfaces'),
        ('get_interfaces_ip', 'Interface IP'),
        ('get_lldp_neighbors', 'LLDP neighbors'),
        ('get_lldp_neighbors_detail', 'LLDP neighbors detail'),
        ('get_mac_address_table', 'MAC address'),
        ('get_ntp_servers', 'NTP servers'),
        ('get_ntp_stats', 'NTP statistics'),
        ('get_optics', 'Transceivers'),
        ('get_snmp_information', 'SNMP'),
        ('get_users', 'Users'),
        ('get_network_instances', 'Network instances (VRF)'),
        ('get_ntp_peers', 'NTP peers'),
        ('get_bgp_config', 'BGP configuration'),
        ('get_bgp_neighbors', 'BGP neighbors'),
        ('get_ipv6_neighbors_table', 'IPv6')
    )
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {
        'polymorphic_identity': 'NapalmGettersService',
    }

    def job(self, device, payload):
        napalm_driver, result = napalm_connection(self, device), {}
        napalm_driver.open()
        for getter in self.getters:
            try:
                result[getter] = getattr(napalm_driver, getter)()
            except Exception as e:
                result[getter] = f'{getter} failed because of {e}'
        output, match = str(result), substitute(self.content_match, locals())
        success = (
            self.content_match_regex and bool(search(match, output))
            or match in output and not self.content_match_regex
        )
        napalm_driver.close()
        return {'success': success, 'result': result}


service_classes['NapalmGettersService'] = NapalmGettersService
