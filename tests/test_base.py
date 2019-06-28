from logging import CRITICAL, disable
from flask.testing import FlaskClient
from typing import Callable

disable(CRITICAL)

pages: tuple = (
    "/administration",
    "/calendar",
    "/dashboard",
    "/login",
    "/table/changelog",
    "/table/configuration",
    "/table/device",
    "/table/link",
    "/table/event",
    "/table/pool",
    "/table/service",
    "/table/user",
    "/table/server",
    "/table/syslog",
    "/table/task",
    "/table/workflow",
    "/view/network",
    "/view/site",
    "/workflow_builder",
)

free_access_pages = {"/", "/login"}


def check_pages(*pages: str) -> Callable:
    def decorator(function: Callable) -> Callable:
        def wrapper(user_client: FlaskClient) -> None:
            function(user_client)
            for page in pages:
                r = user_client.get(page, follow_redirects=True)
                assert r.status_code == 200

        return wrapper

    return decorator


def test_authentication(base_client: FlaskClient) -> None:
    for page in pages:
        expected_code = 200 if page in free_access_pages else 403
        r = base_client.get(page)
        assert r.status_code == expected_code


def test_urls(user_client: FlaskClient) -> None:
    for page in pages:
        r = user_client.get(page, follow_redirects=True)
        assert r.status_code == 200
    r = user_client.get("/logout", follow_redirects=True)
    test_authentication(user_client)
