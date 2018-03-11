from tasks.models import Task
from test_base import check_blueprints
from test_objects import create_from_file
from werkzeug.datastructures import ImmutableMultiDict

getters_once_dict = ImmutableMultiDict([
    ('name', 'getters_once'),
    ('getters', 'get_arp_table'),
    ('getters', 'get_interfaces_counters'),
    ('getters', 'get_interfaces'),
    ('getters', 'get_lldp_neighbors'),
    ('scheduled_date', ''),
    ('frequency', ''),
    ('script_type', 'napalm_getters')
])

getters_recurrent = ImmutableMultiDict([
    ('name', 'testzdqdqd'),
    ('getters', 'get_network_instances'),
    ('getters', 'get_ntp_peers'),
    ('getters', 'get_bgp_config'),
    ('getters', 'get_bgp_neighbors'),
    ('scheduled_date', '15/03/2020 20:47:15'),
    ('frequency', '160'),
    ('script_type', 'napalm_getters')
])

@check_blueprints('/', '/views/', '/tasks/')
def test_getters(user_client):
    create_from_file(user_client, 'europe.xls')
    with user_client.session_transaction() as sess:
        sess['selection'] = ['1', '21', '22']
    user_client.post('views/geographical_view', data=getters_once_dict)
    assert len(Task.query.all()) == 1
