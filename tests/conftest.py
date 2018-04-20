from os import remove
from os.path import abspath, dirname, join, pardir
from sys import path
import pytest

path_source = dirname(abspath(__file__))
path_parent = abspath(join(path_source, pardir))
path_app = join(path_parent, 'source')
path_projects = join(path_parent, 'projects')
path_scripts = join(path_parent, 'scripts')
path_ge = join(path_parent, 'google_earth')
if path_app not in path:
    path.append(path_app)

from flask_app import create_app


@pytest.fixture
def base_client():
    app = create_app(test=True)
    yield app.test_client()
    remove(join(path_source, 'database.db'))


@pytest.fixture
def user_client():
    app = create_app(test=True)
    client = app.test_client()
    create = {'name': 'test', 'password': '', 'create_account': ''}
    login = {'name': 'test', 'password': '', 'login': ''}
    with app.app_context():
        client.post('/admin/process_user', data=create)
        client.post('/admin/login', data=login)
        yield client
    remove(join(path_source, 'database.db'))
