from eNMS import app
from eNMS.database import db

from tests.conftest import check_pages


def test_authentication(base_client):
    for page in app.rbac["get_requests"]:
        r = base_client.get(page)
        assert r.status_code in (200, 302)


def test_urls(user_client):
    for page in app.rbac["get_requests"]:
        if "download" in page:
            continue
        r = user_client.get(page, follow_redirects=True)
        assert r.status_code == 200
    r = user_client.get("/logout", follow_redirects=True)
    test_authentication(user_client)


@check_pages("table/user")
def test_user_management(user_client):
    for user in ("user1", "user2", "user3"):
        dict_user = {
            "form_type": "user",
            "name": user,
            "email": f"{user}@test.com",
            "password": user,
            "theme": "dark",
        }
        user_client.post("/update/user", data=dict_user)
    assert len(db.fetch_all("user")) == 8
    user1 = db.fetch("user", name="user1")
    user_client.post("/delete_instance/user/{}".format(user1.id))
    assert len(db.fetch_all("user")) == 7
