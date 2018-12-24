from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    PickleType,
    String
)
from sqlalchemy.ext.mutable import MutableDict, MutableList

from eNMS.automation.helpers import NAPALM_DRIVERS
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class NapalmGettersService(Service):

    __tablename__ = 'NapalmGettersService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    validation_method = Column(String, default='text')
    validation_method_values = (
        ('text', 'Validation by text match'),
        ('dict_equal', 'Validation by dictionnary equality'),
        ('dict_included', 'Validation by dictionnary inclusion')
    )
    content_match = Column(String)
    content_match_textarea = True
    content_match_regex = Column(Boolean)
    dict_match = Column(MutableDict.as_mutable(PickleType), default={})
    negative_logic = Column(Boolean)
    delete_spaces_before_matching = Column(Boolean)
    driver = Column(String)
    driver_values = NAPALM_DRIVERS
    use_device_driver = Column(Boolean, default=True)
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
        ('get_ipv6_neighbors_table', 'IPv6'),
        ('is_alive', 'Is alive')
    )
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {
        'polymorphic_identity': 'NapalmGettersService',
    }

    def job(self, device, _):
        napalm_driver, result = self.napalm_connection(device), {}
        napalm_driver.open()
        for getter in self.getters:
            try:
                result[getter] = getattr(napalm_driver, getter)()
            except Exception as e:
                result[getter] = f'{getter} failed because of {e}'
        if self.validation_method == 'text':
            success = self.match_content(
                str(result),
                self.sub(self.content_match, locals())
            )
        else:
            success = self.match_dictionnary(result)
        napalm_driver.close()
        return {
            'negative_logic': self.negative_logic,
            'result': result,
            'success': success
        }


service_classes['NapalmGettersService'] = NapalmGettersService
