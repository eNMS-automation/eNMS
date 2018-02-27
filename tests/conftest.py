from os import remove
from os.path import abspath, dirname, join, pardir
from sys import dont_write_bytecode, path
from werkzeug.datastructures import ImmutableMultiDict
import pytest
import tempfile

path_source = dirname(abspath(__file__))
path_parent = abspath(join(path_source, pardir))
path_app = join(path_parent, 'source')
path_projects = join(path_parent, 'projects')
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
    with app.app_context():
        create = ImmutableMultiDict([('username', 'cisco'), ('password', 'cisco'), ('create_account', '')])
        login = ImmutableMultiDict([('username', 'cisco'), ('password', 'cisco'), ('login', '')])
        r = client.post('/users/create_account', data=create)
        client.post('/users/login', data=login)
        yield client
    remove(join(path_source, 'database.db'))