from os import close, unlink
from os.path import abspath, dirname, join, pardir
from sys import dont_write_bytecode, path
import pytest
import tempfile

path_source = dirname(abspath(__file__))
path_parent = abspath(join(path_source, pardir))
path_app = join(path_parent, 'source')
if path_app not in path:
    path.append(path_app)

from flask_app import create_app

@pytest.fixture
def client():
    app = create_app(test=True)
    yield app.test_client()

@pytest.fixture
def client():
    app = create_app(test=True)
    yield app.test_client()
