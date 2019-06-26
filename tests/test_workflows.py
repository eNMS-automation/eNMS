from flask.testing import FlaskClient

from eNMS.database.functions import fetch, fetch_all

from tests.test_base import check_pages


@check_pages("table/workflow_builder")
def test_workflow_creation(user_client: FlaskClient) -> None:
    for workflow in fetch_all("Workflow"):
        assert netmiko_workflow.run()[0]["success"]
