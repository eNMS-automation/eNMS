from collections import OrderedDict

napalm_dispatcher = {
                    # Ax: ASR1000, IOS XE
                    'BNET-A1': ('192.168.243.78', 'ios'),
                    'BNET-A2': ('192.168.243.79', 'ios'),
                    'BNET-A3': ('192.168.243.69', 'ios'),
                    'BNET-A4': ('192.168.243.135', 'ios'),
                    # # C10K, IOS
                    'BNET-E1': ('192.168.243.101', 'ios'),
                    'BNET-E2': ('192.168.243.102', 'ios'),
                    'BNET-E3': ('192.168.243.103', 'ios'),
                    'BNET-E4': ('192.168.243.104', 'ios'),
                    'BNET-E5': ('192.168.243.105', 'ios'),
                    'BNET-E6': ('192.168.243.106', 'ios'),
                    'BNET-E7': ('192.168.243.107', 'ios'),
                    # # C7600, IOS
                    'BNET-I1': ('192.168.243.108', 'ios'),
                    'BNET-I2': ('192.168.243.110', 'ios'),
                    'BNET-I3': ('192.168.243.115', 'ios'),
                    'BNET-I4': ('192.168.243.116', 'ios'),
                    'BNET-I5': ('192.168.243.119', 'ios'),
                    # Gx: GSR12K, IOS XR
                    'BNET-G1': ('192.168.243.21', 'ios-xr'),
                    'BNET-G2': ('192.168.243.22', 'ios-xr'),
                    # ASR9K, IOS XR 
                    'BNET-P1': ('192.168.243.23', 'ios-xr'),
                    # Juniper devices, Junos
                    'BNET-J1': ('192.168.243.77', 'junos'),
                    'BNET-J2': ('192.168.243.82', 'junos'),
                    'BNET-J3': ('192.168.243.83', 'junos'),
                    'BNET-J4': ('192.168.243.117', 'junos'),
                    'BNET-J5': ('192.168.243.118', 'junos'),
                    'BNET-J6': ('192.168.243.133', 'junos'),
                    # Cisco RR, ASK1K, IOS-XE
                    'BNET-R7': ('192.168.243.80', 'ios'),
                    # Cisco nexus
                    'BNET-N1': ('192.168.243.134', 'nx-os'),
                    }
                    
getters_mapping = OrderedDict([
('ARP table', 'get_arp_table'),
('Interfaces counters', 'get_interfaces_counters'),
('Facts', 'get_facts'),
('Environment', 'get_environment'),
('Configuration', 'get_config'),
('Interfaces', 'get_interfaces'),
('Interface IP', 'get_interfaces_ip'),
('LLDP neighbors', 'get_lldp_neighbors'),
('LLDP neighbors detail', 'get_lldp_neighbors_detail'),
('MAC address', 'get_mac_address_table'),
('NTP servers', 'get_ntp_servers'),
('NTP statistics', 'get_ntp_stats'),
('Transceivers', 'get_optics'),
('SNMP', 'get_snmp_information'),
('Users', 'get_users'),
('Network instances (VRF)', 'get_network_instances'),
('NTP peers', 'get_ntp_peers'),
('BGP configuration', 'get_bgp_config'),
('BGP neighbors', 'get_bgp_neighbors'),
('IPv6', 'get_ipv6_neighbors_table'),
])

def str_dict(input, depth=0):
    tab = '\t'*depth
    if isinstance(input, list):
        result = '\n'
        for element in input:
            result += '{}- {}\n'.format(tab, str_dict(element, depth + 1))
        return result
    elif isinstance(input, dict):
        result = ''
        for key, value in input.items():
            result += '\n{}{}: {}'.format(tab, key, str_dict(value, depth + 1))
        return result
    else:
        return str(input)
        
def allowed_file(name, webpage):
    # allowed extensions depending on the webpage
    allowed_extensions = {'devices': {'xls', 'xlsx'}, 'netmiko': {'yaml'}}
    allowed_syntax = '.' in name
    allowed_extension = name.rsplit('.', 1)[1].lower() in allowed_extensions[webpage]
    return allowed_syntax and allowed_extension