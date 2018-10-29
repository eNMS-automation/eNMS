from eNMS import db

from eNMS.logs.models import factory, fetch_all

from tests.test_base import check_blueprints


log1 = ('<189>19: *May  5 05:26:27.523: %LINEPROTO-5-UPDOWN: Line protocol on'
        'Interface FastEthernet0/0, changed state to up')
log2 = ('<189>20: *May  5 05:26:30.275: %LINEPROTO-5-UPDOWN: Line protocol on'
        'Interface FastEthernet0/0, changed state to down')


@check_blueprints('', '/logs')
def test_create_logs(user_client):
    for log in (log1, log2):
        factory('Log', {'ip_address': '192.168.1.88', 'content': log})
    assert len(fetch_all('Log')) == 2
