from pathlib import Path
from pytest import fixture

from config import config_dict
from eNMS import create_app, db


@fixture
def base_client():
    app = create_app(Path.cwd(), config_dict['Debug'])
    app_context = app.app_context()
    app_context.push()
    db.session.close()
    db.drop_all()
    yield app.test_client()


@fixture
def user_client():
    app = create_app(Path.cwd(), config_dict['Debug'])
    app_context = app.app_context()
    app_context.push()
    db.session.close()
    db.drop_all()
    client = app.test_client()
    login = {'name': 'admin', 'password': 'admin'}
    with app.app_context():
        client.post('/admin/login', data=login)
        yield client
