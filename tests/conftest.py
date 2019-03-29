from flask.testing import FlaskClient
from os import remove
from pathlib import Path
from pytest import fixture
from typing import Iterator

from eNMS import create_app, db
from eNMS.config import config_dict


@fixture
def base_client() -> Iterator[FlaskClient]:
    app = create_app(Path.cwd(), config_dict["Debug"])
    app_context = app.app_context()
    app_context.push()
    db.session.close()
    db.drop_all()
    remove(app.path / "eNMS" / "database.db")
    yield app.test_client()
    remove(app.path / "eNMS" / "database.db")


@fixture
def user_client() -> Iterator[FlaskClient]:
    app = create_app(Path.cwd(), config_dict["Debug"])
    app_context = app.app_context()
    app_context.push()
    db.session.close()
    db.drop_all()
    remove(app.path / "eNMS" / "database.db")
    client = app.test_client()
    login = {
        "name": "admin",
        "password": "admin",
        "authentication_method": "Local User",
    }
    with app.app_context():
        client.post("/admin/login", data=login)
        yield client
    remove(app.path / "eNMS" / "database.db")
