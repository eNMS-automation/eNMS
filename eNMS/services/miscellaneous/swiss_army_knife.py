from requests import get
from sqlalchemy import ForeignKey, Integer

from eNMS import app
from eNMS.database import db
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import HiddenField
from eNMS.models.automation import Service


class SwissArmyKnifeService(Service):

    __tablename__ = "swiss_army_knife_service"
    pretty_name = "Swiss Army Knife"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "swiss_army_knife_service"}

    def job(self, *args, **kwargs):
        return getattr(self, self.scoped_name)(*args, **kwargs)

    def Start(self, *args, **kwargs):  # noqa: N802
        return {"success": True}

    def End(self, *args, **kwargs):  # noqa: N802
        return {"success": True}

    def Placeholder(self, *args, **kwargs):  # noqa: N802
        return {"success": True}

    def cluster_monitoring(self, run, payload):
        protocol = app.settings["cluster"]["scan_protocol"]
        for instance in db.fetch_all("instance"):
            db.factory(
                "instance",
                **get(
                    f"{protocol}://{instance.ip_address}/rest/is_alive",
                    timeout=app.settings["cluster"]["scan_timeout"],
                ).json(),
            )
        return {"success": True}

    def process_payload1(self, run, payload, device):
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
