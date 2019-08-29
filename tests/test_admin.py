from flask.testing import FlaskClient

from eNMS import app
from eNMS.database.functions import fetch, fetch_all

from tests.conftest import check_pages


def test_authentication(base_client: FlaskClient) -> None:
    for page in app.valid_pages:
        expected_code = 200 if page in app.free_access_pages else 403
        r = base_client.get(page)
        assert r.status_code == expected_code


def test_urls(user_client: FlaskClient) -> None:
    for page in app.valid_pages:
        r = user_client.get(page, follow_redirects=True)
        assert r.status_code == 200
    r = user_client.get("/logout", follow_redirects=True)
    test_authentication(user_client)


@check_pages("table/user")
def test_user_management(user_client: FlaskClient) -> None:
    for user in ("user1", "user2", "user3"):
        dict_user = {
            "form_type": "user",
            "name": user,
            "email": f"{user}@test.com",
            "permissions": ["Admin"],
            "password": user,
        }
        user_client.post("/update/user", data=dict_user)
    assert len(fetch_all("User")) == 4
    user1 = fetch("User", name="user1")
    user_client.post("/delete_instance/user/{}".format(user1.id))
    assert len(fetch_all("User")) == 3
