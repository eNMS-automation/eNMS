from flask.testing import FlaskClient

from eNMS.database.functions import fetch, fetch_all

from tests.test_base import check_pages


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
