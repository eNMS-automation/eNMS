from flask.testing import FlaskClient
from werkzeug.datastructures import ImmutableMultiDict

from eNMS.database.functions import fetch_all

from tests.test_base import check_pages


@check_pages("table/workflow")
def test_workflow_creation(user_client: FlaskClient) -> None:
    assert len(fetch_all("Workflow")) == 7
