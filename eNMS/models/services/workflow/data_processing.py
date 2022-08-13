from io import StringIO
from jinja2 import Template
from json import loads
from re import findall
from sqlalchemy import ForeignKey, Integer
from textfsm import TextFSM
from warnings import warn
from wtforms.widgets import TextArea

try:
    from ttp import ttp
except ImportError as exc:
    warn(f"Couldn't import ttp module ({exc})")

from eNMS.database import db
from eNMS.forms import ServiceForm
from eNMS.fields import HiddenField, SelectField, StringField
from eNMS.models.automation import Service


class DataProcessingService(Service):

    __tablename__ = "data_processing_service"
    pretty_name = "Data Processing"
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

    __mapper_args__ = {"polymorphic_identity": "data_processing_service"}

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
            if match_type == "regex":
                value = findall(match, value)
            elif "textfsm" in match_type:
                template = TextFSM(StringIO(match))
                value = template.ParseText(value)
                if match_type == "textfsm_dict":
                    value = [dict(zip(template.header, row)) for row in value]
            elif match_type == "jinja2":
                template = Template(match)
                value = template.render(value)
            elif match_type == "ttp":
                parser = ttp(data=value, template=match)
                parser.parse()
                value = loads(parser.result(format="json")[0])
            kwargs = {"device": getattr(device, "name", None), "operation": operation}
            run.payload_helper(variable, value, **kwargs)
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
    ("jinja2", "Apply Jinja2 Template (text output)"),
    ("ttp", "Apply TTP Template (JSON output)"),
    ("textfsm", "Apply TextFSM Template (list output)"),
    ("textfsm_dict", "Apply TextFSM Template (JSON output)"),
)

operation_choices = (
    ("__setitem__", "Set / Replace"),
    ("append", "Append to a list"),
    ("extend", "Extend list"),
    ("update", "Update dictionary"),
)

match_label = (
    "Regular Expression / TextFSM Template Text / Jinja2 Template / TTP Template"
)


class DataProcessingForm(ServiceForm):
    form_type = HiddenField(default="data_processing_service")
    variable1 = StringField("Variable Name")
    query1 = StringField("Variable", python=True)
    match_type1 = SelectField("Processing", choices=match_choices)
    match1 = StringField(match_label, widget=TextArea(), render_kw={"rows": 5})
    operation1 = SelectField("Operation", choices=operation_choices)
    variable2 = StringField("Variable Name")
    query2 = StringField("Variable", python=True)
    match_type2 = SelectField("Processing", choices=match_choices)
    match2 = StringField(match_label, widget=TextArea(), render_kw={"rows": 5})
    operation2 = SelectField("Operation", choices=operation_choices)
    variable3 = StringField("Variable Name")
    query3 = StringField("Variable", python=True)
    match_type3 = SelectField("Processing", choices=match_choices)
    match3 = StringField(match_label, widget=TextArea(), render_kw={"rows": 5})
    operation3 = SelectField("Operation", choices=operation_choices)
    groups = {
        "Processing 1": {
            "commands": ["variable1", "query1", "match_type1", "match1", "operation1"],
            "default": "expanded",
        },
        "Processing 2": {
            "commands": ["variable2", "query2", "match_type2", "match2", "operation2"],
            "default": "expanded",
        },
        "Processing 3": {
            "commands": ["variable3", "query3", "match_type3", "match3", "operation3"],
            "default": "expanded",
        },
    }
