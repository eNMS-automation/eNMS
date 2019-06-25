from flask.testing import FlaskClient
from pathlib import Path
from pytest import fixture
from typing import Iterator

from eNMS import create_app
from eNMS.database import Session


@fixture
def base_client() -> Iterator[FlaskClient]:
    app = create_app(Path.cwd(), "Test")
    app_context = app.app_context()
    app_context.push()
    Session.close()
    yield app.test_client()


@fixture
def user_client() -> Iterator[FlaskClient]:
    app = create_app(Path.cwd(), "Test")
    app_context = app.app_context()
    app_context.push()
    Session.close()
    client = app.test_client()
    with app.app_context():
        client.post(
            "/login",
            data={
                "name": "admin",
                "password": "admin",
                "authentication_method": "Local User",
            },
        )
        yield client
