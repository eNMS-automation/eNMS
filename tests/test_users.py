from users.models import TacacsServer, User
from test_base import check_blueprints
from werkzeug.datastructures import ImmutableMultiDict


@check_blueprints('', '/users')
def test_user_management(user_client):
    for user in ('user1', 'user2', 'user3'):
        dict_user = {
            'username': user,
            'email': '{}@test.com'.format(user),
            'access_rights': 'Read-only',
            'password': user,
            'add_user': ''
        }
        user_client.post('/users/manage_users', data=dict_user)
    assert len(User.query.all()) == 4
    # single user deletion
    delete_user1 = {'users': 'user1', 'delete_user': ''}
    user_client.post('/users/manage_users', data=delete_user1)
    assert len(User.query.all()) == 3
    # multiple user deletion
    delete_users_2_3 = ImmutableMultiDict([
        ('users', 'user2'),
        ('users', 'user3'),
        ('delete_user', '')
    ])
    user_client.post('/users/manage_users', data=delete_users_2_3)
    assert len(User.query.all()) == 1


@check_blueprints('', '/users')
def test_tacacs_configuration(user_client):
    tacacs_server = {
        'ip_address': '192.168.1.2',
        'password': 'test',
        'port': '49',
        'timeout': '10'
    }
    user_client.post('/users/tacacs_server', data=tacacs_server)
    assert len(TacacsServer.query.all()) == 1
