
from sqlalchemy import Column, Float, ForeignKey, Integer, String

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
        ('ARP table': 'get_arp_table',
        ('Interfaces counters': 'get_interfaces_counters',
        ('Facts': 'get_facts',
        ('Environment': 'get_environment',
        ('Configuration': 'get_config',
        ('Interfaces': 'get_interfaces',
        ('Interface IP': 'get_interfaces_ip',
        ('LLDP neighbors': 'get_lldp_neighbors',
        ('LLDP neighbors detail': 'get_lldp_neighbors_detail',
        ('MAC address': 'get_mac_address_table',
        ('NTP servers': 'get_ntp_servers',
        ('NTP statistics': 'get_ntp_stats',
        ('Transceivers': 'get_optics',
        ('SNMP': 'get_snmp_information',
        ('Users': 'get_users',
        ('Network instances (VRF)': 'get_network_instances',
        ('NTP peers': 'get_ntp_peers',
        ('BGP configuration': 'get_bgp_config',
        ('BGP neighbors': 'get_bgp_neighbors',
        ('IPv6': 'get_ipv6_neighbors_table'
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
