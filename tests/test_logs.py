from flask.testing import FlaskClient

from eNMS.controller import controller
from eNMS.database import Session
from eNMS.database.functions import fetch_all

from tests.test_base import check_pages


@check_pages("table/log")
def test_create_logs(user_client: FlaskClient) -> None:
    number_of_logs = len(fetch_all("Changelog"))
    for i in range(10):
        controller.log("warning", str(i))
        Session.commit()
    assert len(fetch_all("Changelog")) == number_of_logs + 10
