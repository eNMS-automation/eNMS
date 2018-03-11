from users.models import User
from test_base import check_blueprints
from werkzeug.datastructures import ImmutableMultiDict


@check_blueprints('/', '/users/')
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
