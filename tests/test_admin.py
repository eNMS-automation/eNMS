from admin.models import SyslogServer, TacacsServer, User
from test_base import check_blueprints
from werkzeug.datastructures import ImmutableMultiDict


@check_blueprints('', '/admin')
def test_user_management(user_client):
    for user in ('user1', 'user2', 'user3'):
        dict_user = {
            'name': user,
            'email': '{}@test.com'.format(user),
            'access_rights': 'Read-only',
            'password': user,
        }
        user_client.post('/admin/process_user', data=dict_user)
    assert len(User.query.all()) == 4
    # user deletion
    user_client.post('/admin/delete_user1')
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


@check_blueprints('', '/admin')
def test_syslog_server(user_client):
    syslog_server = ImmutableMultiDict([
        ('ip_address', '0.0.0.0'),
        ('port', '514')
    ])
    user_client.post('/admin/save_syslog_server', data=syslog_server)
    assert len(SyslogServer.query.all()) == 1
