from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from wtforms import BooleanField, HiddenField, StringField

from eNMS.controller import controller
from eNMS.database import (
    CustomMediumBlobPickle,
    LARGE_STRING_LENGTH,
    SMALL_STRING_LENGTH,
)
from eNMS.forms.automation import ServiceForm
from eNMS.forms.services import ValidationForm
from eNMS.models.automation import Run, Service
from eNMS.models.inventory import Device


class PayloadValidationService(Service):

    __tablename__ = "PayloadValidationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    query = Column(SmallString, default="")
    conversion_method = Column(SmallString, default="text")
    validation_method = Column(SmallString, default="text")
    content_match = Column(LargeString, default="")
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict.as_mutable(CustomMediumBlobPickle), default={})
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "PayloadValidationService"}

    def job(self, run: "Run", payload: dict, device: Optional[Device] = None) -> dict:
        eval_result = controller.eval(run.query, run, **locals())
        result = run.convert_result(eval_result)
        match = (
            run.sub(run.content_match, locals())
            if run.validation_method == "text"
            else run.sub(run.dict_match, locals())
        )
        return {
            "query": run.query,
            "match": match,
            "negative_logic": run.negative_logic,
            "result": result,
            "success": run.match_content(result, match),
        }


class PayloadValidationForm(ServiceForm, ValidationForm):
    form_type = HiddenField(default="PayloadValidationService")
    has_targets = BooleanField("Has Target Devices")
    query = StringField("Python Query")
