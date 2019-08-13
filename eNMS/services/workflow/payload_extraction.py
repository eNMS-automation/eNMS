from io import StringIO
from re import findall
from sqlalchemy import Boolean, Column, ForeignKey, Integer
from textfsm import TextFSM
from typing import Optional
from wtforms import BooleanField, HiddenField, SelectField, StringField
from wtforms.widgets import TextArea

from eNMS.controller import controller
from eNMS.database.dialect import LargeString, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Run, Service
from eNMS.models.inventory import Device


class PayloadExtractionService(Service):

    __tablename__ = "PayloadExtractionService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    variable1 = Column(SmallString)
    query1 = Column(SmallString)
    match_type1 = Column(SmallString, default="none")
    match1 = Column(LargeString, default="")
    variable2 = Column(SmallString)
    query2 = Column(SmallString)
    match_type2 = Column(SmallString, default="none")
    match2 = Column(LargeString, default="")
    variable3 = Column(SmallString)
    query3 = Column(SmallString)
    match_type3 = Column(SmallString, default="none")
    match3 = Column(LargeString, default="")

    __mapper_args__ = {"polymorphic_identity": "PayloadExtractionService"}

    def job(self, run: "Run", payload: dict, device: Optional[Device] = None) -> dict:
        result, success = {}, True
        for i in range(1, 4):
            variable = getattr(run, f"variable{i}")
            if not variable:
                continue
            query = getattr(run, f"query{i}")
            try:
                variables = locals()
                variables.pop("query")
                value = controller.eval(query, run, **variables)
            except Exception as exc:
                success = False
                result[variable] = f"Wrong Python query for {variable} ({exc})"
                continue
            match_type = getattr(run, f"match_type{i}")
            match = getattr(run, f"match{i}")
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
    query1 = StringField("Python query 1")
    match_type1 = SelectField(choices=match_choices)
    match1 = StringField(widget=TextArea(), render_kw={"rows": 5})
    variable2 = StringField()
    query2 = StringField("Python query 2")
    match_type2 = SelectField(choices=match_choices)
    match2 = StringField(widget=TextArea(), render_kw={"rows": 5})
    variable3 = StringField()
    query3 = StringField("Python query 3")
    match_type3 = SelectField(choices=match_choices)
    match3 = StringField(widget=TextArea(), render_kw={"rows": 5})
