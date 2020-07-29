from eNMS import app
from eNMS.database import db

from tests.conftest import check_pages

ignored_endpoints = [
    "/download",
    "/form/alerts_table",
    "/form/calendar",
    "/form/compare",
    "/form/device_data",
    "/form/git_history",
    "/form/instance_deletion",
    "/form/logs",
    "/form/result",
    "/form/table",
    "/form/tree",
    "/logout",
    "/rest/",
    "/view_service_results",
]


def test_authentication(base_client):
    for page in app.rbac["get_requests"]:
        if any(endpoint in page for endpoint in ignored_endpoints):
            continue
        r = base_client.get(page)
        assert r.status_code in (200, 302)


def test_urls(user_client):
    for page in app.rbac["get_requests"]:
        if any(endpoint in page for endpoint in ignored_endpoints):
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
            "authentication": "database",
            "theme": "dark",
        }
        user_client.post("/update/user", data=dict_user)
    assert len(db.fetch_all("user")) == 8
    user1 = db.fetch("user", name="user1")
    user_client.post("/delete_instance/user/{}".format(user1.id))
    assert len(db.fetch_all("user")) == 7
