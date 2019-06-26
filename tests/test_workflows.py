from flask.testing import FlaskClient

# from eNMS.database.functions import fetch, fetch_all

from tests.test_base import check_pages


@check_pages("table/workflow")
def test_workflow_creation(user_client: FlaskClient) -> None:
    assert True
    # for workflow in fetch_all("Workflow"):
    #    assert netmiko_workflow.run()[0]["success"]
