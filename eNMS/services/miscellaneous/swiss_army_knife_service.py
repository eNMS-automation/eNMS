from git import Repo
from git.exc import GitCommandError
from logging import info
from pathlib import Path
from requests import get
from sqlalchemy import ForeignKey, Integer
from wtforms import HiddenField

from eNMS import app
from eNMS.database.dialect import Column
from eNMS.database.functions import factory, fetch_all
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Service


class SwissArmyKnifeService(Service):

    __tablename__ = "swiss_army_knife_service"
    pretty_name = "Swiss Army Knife"
    id = Column(Integer, ForeignKey("service.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "swiss_army_knife_service"}

    def job(self, *args, **kwargs):
        return getattr(self, self.scoped_name)(*args, **kwargs)

    def Start(self, *args, **kwargs):  # noqa: N802
        return {"success": True}

    def End(self, *args, **kwargs):  # noqa: N802
        return {"success": True}

    def cluster_monitoring(self, run, payload):
        protocol = app.config["cluster"]["scan_protocol"]
        for instance in fetch_all("instance"):
            factory(
                "instance",
                **get(
                    f"{protocol}://{instance.ip_address}/rest/is_alive",
                    timeout=app.config["cluster"]["scan_timeout"],
                ).json(),
            )
        return {"success": True}

    def git_push_configurations(self, run, payload):
        if not app.config["app"]["git_repository"]:
            return
        repo = Repo(Path.cwd() / "network_data")
        try:
            repo.remotes.origin.pull()
            repo.git.add(A=True)
            repo.git.commit(m="Automatic commit (configurations)")
        except GitCommandError as e:
            info(f"Git commit failed ({str(e)}")
        repo.remotes.origin.push()
        return {"success": True}

    def process_payload1(self, run, payload, device):
        # we use the name of the device to get the result for that particular device.
        get_facts = run.get_result("NAPALM: Get Facts", device.name)
        get_interfaces = run.get_result("NAPALM: Get interfaces", device.name)
        uptime_less_than_50000 = get_facts["result"]["get_facts"]["uptime"] < 50000
        mgmg1_is_up = get_interfaces["result"]["get_interfaces"]["Management1"]["is_up"]
        return {
            "success": True,
            "uptime_less_5000": uptime_less_than_50000,
            "Management1 is UP": mgmg1_is_up,
        }


class SwissArmyKnifeForm(ServiceForm):
    form_type = HiddenField(default="swiss_army_knife_service")
