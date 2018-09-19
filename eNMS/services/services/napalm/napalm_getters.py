from re import search
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.ext.mutable import MutableList

from eNMS.services.connections import napalm_connection
from eNMS.services.custom_service import CustomService, service_classes
from eNMS.services.models import multiprocessing


class NapalmGettersService(CustomService):

    __tablename__ = 'NapalmGettersService'

    id = Column(Integer, ForeignKey('CustomService.id'), primary_key=True)
    getters = Column(MutableList.as_mutable(PickleType), default=[])
    content_match = Column(String)
    content_match_regex = Column(Boolean)
    device_multiprocessing = True

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

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_configuration_service',
    }

    @multiprocessing
    def job(self, task, device, results, incoming_payload):
        result = {}
        results['expected'] = self.content_match
        try:
            napalm_driver = napalm_connection(device)
            napalm_driver.open()
            for getter in self.getters:
                try:
                    result[getter] = getattr(napalm_driver, getter)()
                except Exception as e:
                    result[getter] = f'{getter} failed because of {e}'
            if self.content_match_regex:
                success = bool(search(self.content_match, str_dict(result)))
            else:
                success = self.content_match in str_dict(result)
            napalm_driver.close()
        except Exception as e:
            result = f'service did not work:\n{e}'
            success = False
        return success, result, result


service_classes['Napalm Getters Service'] = NapalmGettersService
