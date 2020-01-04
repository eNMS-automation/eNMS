from sqlalchemy import ForeignKey, Integer
from wtforms import HiddenField

from eNMS.database.dialect import Column
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Service


class TopologyImportService(Service):

    __tablename__ = "topology_import"
    pretty_name = "Topology Import"
    id = Column(Integer, ForeignKey("service.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "topology_import"}

    def job(self, run, payload):
        return {"success": True}



class TopologyImportForm(ServiceForm):
    form_type = HiddenField(default="topology_import")
