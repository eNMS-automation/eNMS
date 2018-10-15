from eNMS.admin.models import TacacsServer, User
from eNMS.base.helpers import retrieve
from tests.test_base import check_blueprints


@check_blueprints('', '/admin')
def test_user_management(user_client):
    for user in ('user1', 'user2', 'user3'):
        dict_user = {
            'name': user,
            'email': f'{user}@test.com',
            'permissions': ['Admin'],
            'password': user,
        }
        user_client.post('/admin/process_user', data=dict_user)
    assert len(User.query.all()) == 4
    user1 = retrieve(User, name='user1')
    user_client.post('/admin/delete/{}'.format(user1.id))
    assert len(User.query.all()) == 3


@check_blueprints('', '/admin')
def test_tacacs_configuration(user_client):
    tacacs_server = {
        'ip_address': '192.168.1.2',
        'password': 'test',
        'port': '49',
        'timeout': '10'
    }
    user_client.post('/admin/save_tacacs_server', data=tacacs_server)
    assert len(TacacsServer.query.all()) == 1
