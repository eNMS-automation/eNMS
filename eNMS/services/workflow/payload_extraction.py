from io import StringIO
from re import findall
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from textfsm import TextFSM
from typing import Optional
from wtforms import BooleanField, HiddenField, SelectField, StringField
from wtforms.widgets import TextArea

from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Run, Service
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
                value = run.eval(query, **variables)
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
    ("none", "Use Value as Extracted"),
    ("regex", "Apply Regular Expression (findall)"),
    ("textfsm", "Apply TextFSM Template"),
)


class PayloadExtractionForm(ServiceForm):
    form_type = HiddenField(default="PayloadExtractionService")
    has_targets = BooleanField("Has Target Devices")
    variable1 = StringField("Variable Name")
    query1 = StringField("Python Extraction Query")
    match_type1 = SelectField("Post Processing", choices=match_choices)
    match1 = StringField(
        "Regular Expression / TextFSM Template Text",
        widget=TextArea(),
        render_kw={"rows": 5},
    )
    variable2 = StringField("Variable Name")
    query2 = StringField("Python Extraction Query")
    match_type2 = SelectField("Post Processing", choices=match_choices)
    match2 = StringField(
        "Regular Expression / TextFSM Template Text",
        widget=TextArea(),
        render_kw={"rows": 5},
    )
    variable3 = StringField("Variable Name")
    query3 = StringField("Python Extraction Query")
    match_type3 = SelectField("Post Processing", choices=match_choices)
    match3 = StringField(
        "Regular Expression / TextFSM Template Text",
        widget=TextArea(),
        render_kw={"rows": 5},
    )
    groups = {
        "Extraction 1": ["variable1", "query1", "match_type1", "match1"],
        "Extraction 2": ["variable2", "query2", "match_type2", "match2"],
        "Extraction 3": ["variable3", "query3", "match_type3", "match3"],
    }
