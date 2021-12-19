from eNMS.database import db
from eNMS.variables import vs

from tests.conftest import check_pages

ignored_endpoints = [
    "/alerts_table_form",
    "/calendar_form",
    "/compare_form",
    "/confirmation",
    "/device_data_form",
    "/download",
    "/export_service",
    "/files_form",
    "/git_history_form",
    "/help",
    "/instance_deletion_form",
    "/logs_form",
    "/parameterized",
    "/result_form",
    "/session_log_form",
    "/table_form",
    "/terminal",
    "/tree_form",
    "/instance_tree_form",
    "/logout",
    "/rest/",
    "/result_comparison_form",
    "/view_service_results",
]


def test_authentication(base_client):
    for page in vs.rbac["get_requests"]:
        if any(endpoint in page for endpoint in ignored_endpoints):
            continue
        r = base_client.get(page)
        assert r.status_code in (200, 302)


def test_urls(user_client):
    for page in vs.rbac["get_requests"]:
        if any(endpoint in page for endpoint in ignored_endpoints):
            continue
        r = user_client.get(page, follow_redirects=True)
        assert r.status_code == 200
    r = user_client.get("/logout", follow_redirects=True)
    test_authentication(user_client)


@check_pages("user_table")
def test_user_management(user_client):
    number_of_users = len(db.fetch_all("user"))
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
    assert len(db.fetch_all("user")) == number_of_users + 3
    user1 = db.fetch("user", name="user1")
    user_client.post("/delete_instance/user/{}".format(user1.id))
    assert len(db.fetch_all("user")) == number_of_users + 2
