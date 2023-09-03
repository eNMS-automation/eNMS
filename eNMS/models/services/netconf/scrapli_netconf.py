from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.fields import BooleanField, HiddenField, SelectField, StringField
from eNMS.forms import ConnectionForm
from eNMS.models.automation import ConnectionService


class ScrapliNetconfService(ConnectionService):
    __tablename__ = "scrapli_netconf_service"
    pretty_name = "Scrapli Netconf"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    command = db.Column(db.SmallString)
    target = db.Column(db.SmallString)
    content = db.Column(db.LargeString)
    commit_config = db.Column(Boolean, default=False)
    strip_namespaces = db.Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "scrapli_netconf_service"}

    def job(self, run, device):
        content, kwargs = run.sub(run.content, locals()), {}
        if "lock" in run.command or "config" in run.command:
            parameter = "source" if run.command == "get_config" else "target"
            kwargs[parameter] = run.target
        if run.command in ("edit_config", "get", "rpc"):
            parameter = "config" if run.command == "edit_config" else "filter_"
            kwargs[parameter] = content
        if run.command == "get":
            kwargs["filter_type"] = "subtree"
        response = getattr(run.scrapli_connection(device), run.command)(**kwargs)
        if run.commit_config:
            run.scrapli_connection(device).commit()
        return {"filter_": filter, "kwargs": kwargs, "result": response.result}


class ScrapliNetconfForm(ConnectionForm):
    form_type = HiddenField(default="scrapli_netconf_service")
    command = SelectField(
        choices=(
            ("get", "Get"),
            ("rpc", "RPC"),
            ("get_config", "Get Configuration"),
            ("edit_config", "Edit Configuration"),
            ("delete_config", "Delete Configuration"),
            ("commit", "Commit Configuration"),
            ("discard", "Discard Configuration"),
            ("lock", "Lock"),
            ("unlock", "Unlock"),
        )
    )
    target = SelectField(
        choices=(
            ("running", "Running Configuration"),
            ("startup", "Startup Configuration"),
            ("candidate", "Candidate Configuration"),
        )
    )
    content = StringField(substitution=True, widget=TextArea(), render_kw={"rows": 5})
    commit_config = BooleanField("Commit After Editing Configuration")
    strip_namespaces = BooleanField("Strip Namespaces from returned XML")
    groups = {
        "Main Parameters": {
            "commands": [
                "command",
                "target",
                "content",
                "commit_config",
                "strip_namespaces",
            ],
            "default": "expanded",
        },
        **ConnectionForm.groups,
    }
