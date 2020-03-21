from flask.testing import FlaskClient

from eNMS.database import db

from tests.conftest import check_pages


@check_pages("table/workflow")
def test_configuration_workflow(user_client: FlaskClient):
    workflow = db.fetch("workflow", name="Configuration Management Workflow")
    assert workflow.run()[0]["success"]


@check_pages("table/workflow")
def test_extraction_validation_workflow(user_client: FlaskClient):
    workflow = db.fetch("workflow", name="payload_extraction_validation_worflow")
    assert workflow.run()[0]["success"]


@check_pages("table/workflow")
def test_netmiko_workflow(user_client: FlaskClient):
    workflow = db.fetch("workflow", name="Netmiko_VRF_workflow")
    assert workflow.run()[0]["success"]


@check_pages("table/workflow")
def test_napalm_workflow(user_client: FlaskClient):
    workflow = db.fetch("workflow", name="Napalm_VRF_workflow")
    assert workflow.run()[0]["success"]


@check_pages("table/workflow")
def test_payload_transfer_workflow(user_client: FlaskClient):
    workflow = db.fetch("workflow", name="payload_transfer_workflow")
    assert workflow.run()[0]["success"]


@check_pages("table/workflow")
def test_workflow_of_workflows(user_client: FlaskClient):
    workflow = db.fetch("workflow", name="Workflow_of_workflows")
    assert workflow.run()[0]["success"]


@check_pages("table/workflow")
def test_yaql_test_worflow(user_client: FlaskClient):
    workflow = db.fetch("workflow", name="YaQL_test_worflow")
    assert workflow.run()[0]["success"]
