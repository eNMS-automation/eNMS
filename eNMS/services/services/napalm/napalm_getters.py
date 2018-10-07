from multiprocessing.pool import ThreadPool
from re import search
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableList

from eNMS.services.helpers import napalm_connection, NAPALM_DRIVERS
from eNMS.services.models import Service, service_classes


class NapalmGettersService(Service):

    __tablename__ = 'NapalmGettersService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
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
    operating_system = Column(String)
    vendor = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_getters_service',
    }

    def job(self, task, workflow_results):
        targets = task.compute_targets()
        results = {'success': True, 'devices': {}}
        pool = ThreadPool(processes=len(targets))
        pool.map(self.device_job, [(device, results) for device in targets])
        pool.close()
        pool.join()
        return results

    def device_job(self, args):
        device, results = args
        result = {}
        try:
            napalm_driver = napalm_connection(self, device)
            napalm_driver.open()
            for getter in self.getters:
                try:
                    result[getter] = getattr(napalm_driver, getter)()
                except Exception as e:
                    result[getter] = f'{getter} failed because of {e}'
            if self.content_match_regex:
                success = bool(search(self.content_match, str(result)))
            else:
                success = self.content_match in str(result)
            if not success:
                results['success'] = False
            napalm_driver.close()
        except Exception as e:
            result, success = f'task failed ({e})', False
            results['success'] = False
        results['devices'][device.name] = {
            'success': success,
            'result': result
        }


service_classes['Napalm Getters Service'] = NapalmGettersService
