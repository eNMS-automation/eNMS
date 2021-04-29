from pytest import fixture

from eNMS.database import db
from eNMS.server import server

import warnings


@fixture
def base_client():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        app_context = server.app_context()
        app_context.push()
        db.session.close()
        yield server.test_client()


@fixture
def user_client():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        app_context = server.app_context()
        app_context.push()
        db.session.close()
        client = server.test_client()
        with server.app_context():
            client.post(
                "/login",
                data={
                    "username": "admin",
                    "password": "admin",
                    "authentication_method": "database",
                },
            )
            yield client


def check_pages(*pages):
    def decorator(function):
        def wrapper(user_client):
            function(user_client)
            for page in pages:
                r = user_client.get(page, follow_redirects=True)
                assert r.status_code == 200

        return wrapper

    return decorator
