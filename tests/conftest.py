from flask.testing import FlaskClient
from os import remove
from pathlib import Path
from pytest import fixture
from typing import Iterator

from eNMS import create_app
from eNMS.config import config_dict
from eNMS.database import Base, engine, Session


@fixture
def base_client() -> Iterator[FlaskClient]:
    app = create_app(Path.cwd(), config_dict["Debug"])
    app_context = app.app_context()
    app_context.push()
    Session.close()
    Base.metadata.create_all(bind=engine)
    yield app.test_client()
    remove(app.path / "database.db")


@fixture
def user_client() -> Iterator[FlaskClient]:
    app = create_app(Path.cwd(), config_dict["Debug"])
    app_context = app.app_context()
    app_context.push()
    Session.close()
    Base.metadata.create_all(bind=engine)
    client = app.test_client()
    login = {
        "name": "admin",
        "password": "admin",
        "authentication_method": "Local User",
    }
    with app.app_context():
        client.post("/login", data=login)
        yield client
    remove(app.path / "database.db")
