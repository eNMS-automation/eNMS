from io import StringIO
from re import findall
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from textfsm import TextFSM
from typing import Optional
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
)
from yaql import factory

from eNMS.controller import controller
from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class PayloadExtractionService(Service):

    __tablename__ = "PayloadExtractionService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    variable1 = Column(String(SMALL_STRING_LENGTH), default="")
    query1 = Column(String(SMALL_STRING_LENGTH), default="")
    match_type1 = Column(String(SMALL_STRING_LENGTH), default="")
    match1 = Column(Text(LARGE_STRING_LENGTH), default="")
    variable2 = Column(String(SMALL_STRING_LENGTH), default="")
    query2 = Column(String(SMALL_STRING_LENGTH), default="")
    match_type2 = Column(String(SMALL_STRING_LENGTH), default="")
    match2 = Column(Text(LARGE_STRING_LENGTH), default="")
    variable3 = Column(String(SMALL_STRING_LENGTH), default="")
    query3 = Column(String(SMALL_STRING_LENGTH), default="")
    match_type3 = Column(String(SMALL_STRING_LENGTH), default="")
    match3 = Column(Text(LARGE_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "PayloadExtractionService"}

    def job(self, payload: dict, device: Device, parent: Optional[Job] = None) -> dict:
        result, success = {}, True
        for i in range(1, 4):
            variable = getattr(self, f"variable{i}")
            if not variable:
                continue
            query = getattr(self, f"query{i}")
            engine = factory.YaqlFactory().create()
            value = engine(query).evaluate(data=payload)
            match_type = getattr(self, f"match_type{i}")
            match = getattr(self, f"match{i}")
            result[variable] = {"query": query, "match_type": match_type}
            if match_type == "none":
                result["value"] = value
            elif match_type == "regex":
                result["value"] = findall(match, value)
            else:
                result["value"] = TextFSM(StringIO(match)).ParseText(value)
        return {"result": result, "success": True}


match_choices = (
    ("none", "No post-processing"),
    ("regex", "Regular Expression (findall)"),
    ("textfsm", "TextFSM Template"),
)


class PayloadExtractionForm(ServiceForm):
    form_type = HiddenField(default="PayloadExtractionService")
    variable1 = StringField()
    query1 = StringField()
    match_type1 = SelectField(choices=match_choices)
    match1 = StringField(widget=TextArea(), render_kw={"rows": 5})
    variable2 = StringField()
    query2 = StringField()
    match_type2 = SelectField(choices=match_choices)
    match2 = StringField(widget=TextArea(), render_kw={"rows": 5})
    variable3 = StringField()
    query3 = StringField()
    match_type3 = SelectField(choices=match_choices)
    match3 = StringField(widget=TextArea(), render_kw={"rows": 5})
