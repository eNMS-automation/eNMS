from flask.testing import FlaskClient

from eNMS.database.functions import fetch

from tests.test_base import check_pages


@check_pages("table/workflow")
def test_netmiko_workflow(user_client: FlaskClient) -> None:
    workflow = fetch("Workflow", name="Netmiko_VRF_workflow")
    assert workflow.run()[0]["success"]


@check_pages("table/workflow")
def test_extraction_validation_workflow(user_client: FlaskClient) -> None:
    workflow = fetch("Workflow", name="payload_extraction_validation_worflow")
    assert workflow.run()[0]["success"]
