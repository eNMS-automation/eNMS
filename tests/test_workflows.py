from flask.testing import FlaskClient

from eNMS.database.functions import fetch

from tests.test_base import check_pages


@check_pages("table/workflow")
def test_yaql_test_worflow(user_client: FlaskClient) -> None:
    workflow = fetch("Workflow", name="YaQL_test_worflow")
    assert workflow.run()[0]["success"]
