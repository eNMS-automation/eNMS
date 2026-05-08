from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import relationship

from eNMS.database import db
from eNMS.fields import HiddenField, InstanceField, SelectField
from eNMS.forms import DataForm
from eNMS.models.administration import Data
from eNMS.variables import vs


class Store(Data):
    __tablename__ = "store"
    pretty_name = "Store"
    id = db.Column(Integer, ForeignKey("data.id"), primary_key=True)
    data_type = db.Column(db.SmallString, default="store")
    data = relationship(
        "Data",
        back_populates="store",
        foreign_keys="Data.store_id",
    )
    __mapper_args__ = {
        "polymorphic_identity": "store",
        "inherit_condition": id == Data.id,
    }

    def post_update(self, migration_import=False):
        old_name = self.name
        super().post_update()
        if migration_import or old_name != self.name:
            for datum in self.data:
                datum.post_update()


class StoreForm(DataForm):
    template = "object"
    form_type = HiddenField(default="store")
    id = HiddenField()
    store = InstanceField("Store", model="store", constraints={"data_type": "store"})
    data_type = SelectField("Data Type")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_type.choices = sorted(
            vs.subtypes["data"].items(), key=lambda x: x[0] != "store"
        )
