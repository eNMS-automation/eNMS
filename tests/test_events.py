from werkzeug.datastructures import ImmutableMultiDict

from eNMS import app
from eNMS.database import db

from tests.conftest import check_pages
from tests.test_inventory import create_from_file


instant_task = ImmutableMultiDict(
    [
        ("form_type", "task"),
        ("start_date", "30/03/2018 19:10:13"),
        ("name", "instant_task"),
        ("frequency_unit", "seconds"),
        ("scheduling_mode", "standard"),
        ("service", "2"),
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
        ("service", "2"),
    ]
)


@check_pages("table/task")
def test_netmiko_napalm_config(user_client):
    create_from_file(user_client, "europe.xls")
    user_client.post("/update/task", data=instant_task)
    assert len(db.fetch_all("task")) == 4
    user_client.post("/update/task", data=scheduled_task)
    assert len(db.fetch_all("task")) == 5


@check_pages("table/changelog")
def test_create_logs(user_client):
    number_of_logs = len(db.fetch_all("changelog"))
    for i in range(10):
        app.log("warning", str(i))
    db.session.commit()
    assert len(db.fetch_all("changelog")) == number_of_logs + 11
