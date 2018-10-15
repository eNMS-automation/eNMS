from time import sleep

from eNMS import db
from eNMS.base.helpers import retrieve
from eNMS.automation.models import Workflow

from tests.test_base import check_blueprints


@check_blueprints('/automation')
def netmiko_workflow(user_client):
    workflow = retrieve(Workflow, name='netmiko_VRF_workflow')
    workflow.run()
    sleep(75)
    db.session.commit()
    assert True
