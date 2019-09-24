from werkzeug.datastructures import ImmutableMultiDict

from eNMS import app
from eNMS.database import Session
from eNMS.database.functions import fetch_all

from tests.conftest import check_pages
from tests.test_inventory import create_from_file


instant_task = ImmutableMultiDict(
    [
        ("form_type", "task"),
        ("start_date", "30/03/2018 19:10:13"),
        ("name", "instant_task"),
        ("frequency_unit", "seconds"),
        ("scheduling_mode", "standard"),
        ("job", "2"),
    ]
)

scheduled_task = ImmutableMultiDict(
    [
        ("form_type", "task"),
        ("name", "scheduled_task"),
        ("frequency_unit", "seconds"),
        ("scheduling_mode", "standard"),
        ("start_date", "30/03/2018 19:10:13"),
        ("end_date", "06/04/2018 19:10:13"),
        ("frequency", "3600"),
        ("job", "2"),
    ]
)


@check_pages("table/task", "calendar/task")
def test_netmiko_napalm_config(user_client):
    create_from_file(user_client, "europe.xls")
    user_client.post("/update/task", data=instant_task)
    assert len(fetch_all("Task")) == 3
    user_client.post("/update/task", data=scheduled_task)
    assert len(fetch_all("Task")) == 4


@check_pages("table/changelog")
def test_create_logs(user_client):
    number_of_logs = len(fetch_all("Changelog"))
    for i in range(10):
        app.log("warning", str(i))
        Session.commit()
    assert len(fetch_all("Changelog")) == number_of_logs + 10
