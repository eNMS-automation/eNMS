from sqlalchemy import ForeignKey, Integer

from eNMS.database import db
from eNMS.fields import HiddenField, InstanceField, IntegerField, StringField
from eNMS.forms import DataForm
from eNMS.models.administration import Data


class VLAN(Data):
    __tablename__ = "vlan"
    pretty_name = "VLAN"
    __mapper_args__ = {"polymorphic_identity": "vlan"}
    id = db.Column(Integer, ForeignKey("data.id"), primary_key=True)
    vlan_id = db.Column(Integer, default=1)
    role = db.Column(db.SmallString)
    group = db.Column(db.SmallString)


class VLANForm(DataForm):
    form_type = HiddenField(default="vlan")
    store = InstanceField("Store", model="store", constraints={"data_type": "vlan"})
    vlan_id = IntegerField(
        "VLAN ID",
        default=1,
        layout="""
        <div style="float:right; width: 80%;">
          {field}
        </div>
        <div style="float:right; width: 20%;">
          <center>
            <button
              type="button"
              class="btn-id"
              style="width: 90%; margin-top: 5px"
              value="eNMS.datastore.getNextVlanId">
                Get Next ID
            </button>
          </center>
        </div>""",
    )
    role = StringField()
    group = StringField()
    properties = ["vlan_id", "role", "group"]
