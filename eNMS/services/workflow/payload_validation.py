from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from wtforms import HiddenField, StringField

from eNMS.database import (
    CustomMediumBlobPickle,
    LARGE_STRING_LENGTH,
    SMALL_STRING_LENGTH,
)
from eNMS.forms.automation import ServiceForm
from eNMS.forms.services import ValidationForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class PayloadValidationService(Service):

    __tablename__ = "PayloadValidationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    query = Column(String(SMALL_STRING_LENGTH), default="")
    conversion_method = Column(String(SMALL_STRING_LENGTH), default="text")
    validation_method = Column(String(SMALL_STRING_LENGTH), default="text")
    content_match = Column(Text(LARGE_STRING_LENGTH), default="")
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict.as_mutable(CustomMediumBlobPickle), default={})
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "PayloadValidationService"}

    def job(
        self,
        payload: dict,
        timestamp: str,
        device: Device,
        parent: Optional[Job] = None,
    ) -> dict:
        result = self.convert_result(eval(self.query, locals()))
        match = (
            self.sub(self.content_match, locals())
            if self.validation_method == "text"
            else self.sub(self.dict_match, locals())
        )
        return {
            "query": self.query,
            "match": match,
            "negative_logic": self.negative_logic,
            "result": result,
            "success": self.match_content(result, match),
        }


class PayloadValidationForm(ServiceForm, ValidationForm):
    form_type = HiddenField(default="PayloadValidationService")
    query = StringField("Python Query")
