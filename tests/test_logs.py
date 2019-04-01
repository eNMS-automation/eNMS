from flask.testing import FlaskClient

from eNMS import db
from eNMS.functions import fetch_all
from eNMS.logs.models import Log

from tests.test_base import check_blueprints


log1 = (
    "<189>19: *May  5 05:26:27.523: %LINEPROTO-5-UPDOWN: Line protocol on"
    "Interface FastEthernet0/0, changed state to up"
)
log2 = (
    "<189>20: *May  5 05:26:30.275: %LINEPROTO-5-UPDOWN: Line protocol on"
    "Interface FastEthernet0/0, changed state to down"
)


@check_blueprints("", "/logs")
def test_create_logs(user_client: FlaskClient) -> None:
    for log in (log1, log2):
        kwargs = {"ip_address": "192.168.1.88", "content": log, "log_rules": []}
        log_object = Log(**kwargs)
        db.session.add(log_object)
        db.session.commit()
    assert len(fetch_all("Log")) == 2
