from io import StringIO
from re import findall
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from textfsm import TextFSM
from typing import Optional
from wtforms import BooleanField, HiddenField, SelectField, StringField
from wtforms.widgets import TextArea
from yaql import factory

from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class PayloadExtractionService(Service):

    __tablename__ = "PayloadExtractionService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    variable1 = Column(String(SMALL_STRING_LENGTH), default="")
    query1 = Column(String(SMALL_STRING_LENGTH), default="")
    match_type1 = Column(String(SMALL_STRING_LENGTH), default="none")
    match1 = Column(Text(LARGE_STRING_LENGTH), default="")
    variable2 = Column(String(SMALL_STRING_LENGTH), default="")
    query2 = Column(String(SMALL_STRING_LENGTH), default="")
    match_type2 = Column(String(SMALL_STRING_LENGTH), default="none")
    match2 = Column(Text(LARGE_STRING_LENGTH), default="")
    variable3 = Column(String(SMALL_STRING_LENGTH), default="")
    query3 = Column(String(SMALL_STRING_LENGTH), default="")
    match_type3 = Column(String(SMALL_STRING_LENGTH), default="none")
    match3 = Column(Text(LARGE_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "PayloadExtractionService"}

    def job(
        self,
        payload: dict,
        device: Optional[Device] = None,
        parent: Optional[Job] = None,
    ) -> dict:
        result, success = {}, True
        for i in range(1, 4):
            variable = getattr(self, f"variable{i}")
            if not variable:
                continue
            query = self.sub(getattr(self, f"query{i}"), locals())
            try:
                engine = factory.YaqlFactory().create()
                value = engine(query).evaluate(data=payload)
            except Exception as exc:
                success = False
                result[variable] = f"Wrong YaQL query for {variable} ({exc})"
                continue
            match_type = getattr(self, f"match_type{i}")
            match = getattr(self, f"match{i}")
            result[variable] = {
                "query": query,
                "match_type": match_type,
                "match": match,
                "value": (
                    value
                    if match_type == "none"
                    else findall(match, value)
                    if match_type == "regex"
                    else TextFSM(StringIO(match)).ParseText(value)
                ),
            }
        return {"result": result, "success": success}


match_choices = (
    ("none", "No post-processing"),
    ("regex", "Regular Expression (findall)"),
    ("textfsm", "TextFSM Template"),
)


class PayloadExtractionForm(ServiceForm):
    form_type = HiddenField(default="PayloadExtractionService")
    has_targets = BooleanField("Has Target Devices")
    variable1 = StringField()
    query1 = SubstitutionField()
    match_type1 = SelectField(choices=match_choices)
    match1 = StringField(widget=TextArea(), render_kw={"rows": 5})
    variable2 = StringField()
    query2 = SubstitutionField()
    match_type2 = SelectField(choices=match_choices)
    match2 = StringField(widget=TextArea(), render_kw={"rows": 5})
    variable3 = StringField()
    query3 = SubstitutionField()
    match_type3 = SelectField(choices=match_choices)
    match3 = StringField(widget=TextArea(), render_kw={"rows": 5})
