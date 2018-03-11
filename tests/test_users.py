from users.models import User
from test_base import check_blueprints
from werkzeug.datastructures import ImmutableMultiDict

# ImmutableMultiDict([('username', 'test'), ('email', 'test@test.com'), ('access_rights', 'Read-only'), ('password', 'test'), ('add_user', '')])

# ImmutableMultiDict([('users', 'dqzdqzdqz'), ('users', 'dqzdqzdqzdqzdq'), ('delete_user', '')])

@check_blueprints('/', '/users/')
def test_user_creation(user_client):
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

# 
# @check_blueprints('/', '/users/')
# def test_user_deletion(user_client):
#     # single user deletion
#     create_from_file(user_client, 'europe.xls')
#     user_client.post('/objects/object_deletion', data=links)
#     assert len(Node.query.all()) == 33
#     assert len(Link.query.all()) == 38
