from io import StringIO
from re import findall
from sqlalchemy import ForeignKey, Integer
from textfsm import TextFSM
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.forms import ServiceForm
from eNMS.fields import HiddenField, SelectField, StringField
from eNMS.models.automation import Service


class DataExtractionService(Service):

    __tablename__ = "data_extraction_service"
    pretty_name = "Data Extraction"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    variable1 = db.Column(db.SmallString)
    query1 = db.Column(db.SmallString)
    match_type1 = db.Column(db.SmallString, default="none")
    match1 = db.Column(db.LargeString)
    operation1 = db.Column(db.SmallString, default="__setitem__")
    variable2 = db.Column(db.SmallString)
    query2 = db.Column(db.SmallString)
    match_type2 = db.Column(db.SmallString, default="none")
    match2 = db.Column(db.LargeString)
    operation2 = db.Column(db.SmallString, default="__setitem__")
    variable3 = db.Column(db.SmallString)
    query3 = db.Column(db.SmallString)
    match_type3 = db.Column(db.SmallString, default="none")
    match3 = db.Column(db.LargeString)
    operation3 = db.Column(db.SmallString, default="__setitem__")

    __mapper_args__ = {"polymorphic_identity": "data_extraction_service"}

    def job(self, run, device=None):
        result, success = {}, True
        for index in range(1, 4):
            variable = getattr(run, f"variable{index}")
            if not variable:
                continue
            query = getattr(run, f"query{index}")
            try:
                variables = locals()
                variables.pop("query")
                value = run.eval(query, **variables)[0]
            except Exception as exc:
                success = False
                result[variable] = f"Wrong Python query for {variable} ({exc})"
                continue
            match_type = getattr(run, f"match_type{index}")
            match = getattr(run, f"match{index}")
            operation = getattr(run, f"operation{index}")
            value = (
                value
                if match_type == "none"
                else findall(match, value)
                if match_type == "regex"
                else TextFSM(StringIO(match)).ParseText(value)
            )
            run.payload_helper(variable, value, device=device.name, operation=operation)
            result[variable] = {
                "query": query,
                "match_type": match_type,
                "match": match,
                "value": value,
            }
        return {"result": result, "success": success}


match_choices = (
    ("none", "Use Value as Extracted"),
    ("regex", "Apply Regular Expression (findall)"),
    ("textfsm", "Apply TextFSM Template"),
)

operation_choices = (
    ("__setitem__", "Set / Replace"),
    ("append", "Append to a list"),
    ("extend", "Extend list"),
    ("update", "Update dictionary"),
)


class DataExtractionForm(ServiceForm):
    form_type = HiddenField(default="data_extraction_service")
    variable1 = StringField("Variable Name")
    query1 = StringField("Python Extraction Query", python=True)
    match_type1 = SelectField("Post Processing", choices=match_choices)
    match1 = StringField(
        "Regular Expression / TextFSM Template Text",
        widget=TextArea(),
        render_kw={"rows": 5},
    )
    operation1 = SelectField("Operation", choices=operation_choices)
    variable2 = StringField("Variable Name")
    query2 = StringField("Python Extraction Query", python=True)
    match_type2 = SelectField("Post Processing", choices=match_choices)
    match2 = StringField(
        "Regular Expression / TextFSM Template Text",
        widget=TextArea(),
        render_kw={"rows": 5},
    )
    operation2 = SelectField("Operation", choices=operation_choices)
    variable3 = StringField("Variable Name")
    query3 = StringField("Python Extraction Query", python=True)
    match_type3 = SelectField("Post Processing", choices=match_choices)
    match3 = StringField(
        "Regular Expression / TextFSM Template Text",
        widget=TextArea(),
        render_kw={"rows": 5},
    )
    operation3 = SelectField("Operation", choices=operation_choices)
    groups = {
        "Extraction 1": {
            "commands": ["variable1", "query1", "match_type1", "match1", "operation1"],
            "default": "expanded",
        },
        "Extraction 2": {
            "commands": ["variable2", "query2", "match_type2", "match2", "operation2"],
            "default": "expanded",
        },
        "Extraction 3": {
            "commands": ["variable3", "query3", "match_type3", "match3", "operation3"],
            "default": "expanded",
        },
    }
