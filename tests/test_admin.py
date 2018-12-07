from eNMS.base.helpers import fetch, fetch_all
from tests.test_base import check_blueprints


@check_blueprints('', '/admin')
def test_user_management(user_client):
    for user in ('user1', 'user2', 'user3'):
        dict_user = {
            'list_fields': 'permissions',
            'name': user,
            'email': f'{user}@test.com',
            'permissions': ['Admin'],
            'password': user
        }
        user_client.post('/update/user', data=dict_user)
    assert len(fetch_all('User')) == 4
    user1 = fetch('User', name='user1')
    user_client.post('/delete/user/{}'.format(user1.id))
    assert len(fetch_all('User')) == 3
