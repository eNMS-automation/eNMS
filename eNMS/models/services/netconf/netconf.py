from json import dumps
from sqlalchemy import Boolean, ForeignKey, Integer
import xmltodict
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.fields import (
    BooleanField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
)
from eNMS.forms import ConnectionForm
from eNMS.models.automation import ConnectionService


class NetconfService(ConnectionService):
    __tablename__ = "netconf_service"
    pretty_name = "Netconf (ncclient)"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    nc_type = db.Column(db.SmallString)
    target = db.Column(db.SmallString)
    default_operation = db.Column(db.SmallString)
    test_option = db.Column(db.SmallString)
    error_option = db.Column(db.SmallString)
    xml_filter = db.Column(db.LargeString, default="")
    lock = db.Column(Boolean, default=False)
    unlock = db.Column(Boolean, default=False)
    commit_conf = db.Column(Boolean, default=False)
    copy_source = db.Column(db.SmallString)
    source_url = db.Column(db.SmallString)
    copy_destination = db.Column(db.SmallString)
    destination_url = db.Column(db.SmallString)
    xml_conversion = db.Column(Boolean, default=True)

    __mapper_args__ = {"polymorphic_identity": "netconf_service"}

    def job(self, run, device=None):
        xml_filter = run.sub(run.xml_filter, locals())
        run.log("info", "Sending NETCONF request", device, logger="security")
        result = {"success": False, "result": "No NETCONF operation selected."}
        manager = run.ncclient_connection(device)
        if run.lock:
            manager.lock(target=run.target)
        if run.nc_type == "get_config":
            result = manager.get_config(source=run.target).data_xml
        if run.nc_type == "get_filtered_config":
            result = manager.get(str(xml_filter)).data_xml
        if run.nc_type == "push_config":
            result = manager.edit_config(
                target=run.target,
                config=str(xml_filter),
                default_operation=None
                if run.default_operation == "None"
                else run.default_operation,
                test_option=None if run.test_option == "None" else run.test_option,
                error_option=None if run.error_option == "None" else run.error_option,
            )
        if run.nc_type == "copy_config":
            result = manager.copy_config(
                source=run.source_url
                if run.copy_source == "source_url"
                else run.copy_source,
                target=run.destination_url
                if run.copy_destination == "destination_url"
                else run.copy_destination,
            )
        if run.commit_conf:
            manager.commit()
        if run.nc_type == "rpc":
            result = manager.rpc(str(xml_filter)).data_xml
        if run.xml_conversion:
            result = xmltodict.parse(str(result))
        if run.unlock:
            manager.unlock(target=run.target)
        return {"success": True, "result": result}


class NetconfForm(ConnectionForm):
    form_type = HiddenField(default="netconf_service")
    nc_type = SelectField(
        choices=(
            ("get_config", "Get Full Config"),
            ("get_filtered_config", "Get"),
            ("push_config", "Edit Config"),
            ("copy_config", "Copy Config"),
            ("rpc", "Dispatch"),
        ),
        label="NETCONF Operation",
    )
    xml_filter = StringField(
        label="XML Filter", widget=TextArea(), render_kw={"rows": 5}, substitution=True
    )
    target = SelectField(
        choices=(
            ("running", "Running"),
            ("candidate", "Candidate"),
            ("startup", "Startup"),
        ),
        label="Target Config",
    )
    default_operation = SelectField(
        choices=(
            ("merge", "Merge"),
            ("replace", "Replace"),
            ("None", "None"),
        ),
        label="Default config operation",
        validate_choice=False,
    )
    test_option = SelectField(
        choices=(
            ("test-then-set", "Test, then set"),
            ("set", "Set"),
            ("None", "None"),
        ),
        label="Config test option",
        validate_choice=False,
    )
    error_option = SelectField(
        choices=(
            ("stop-on-error", "Stop on error"),
            ("continue-on-error", "Continue on error"),
            ("rollback-on-error", "Rollback on error"),
            ("None", "None"),
        ),
        label="Error option",
        validate_choice=False,
    )
    lock = BooleanField(label="Lock target")
    unlock = BooleanField(label="Unlock target")
    copy_source = SelectField(
        choices=(
            ("running", "Running"),
            ("candidate", "Candidate"),
            ("startup", "Startup"),
            ("source_url", "Source URL"),
        ),
        label="Copy Source",
        validate_choice=False,
    )
    source_url = StringField(
        label="Copy source URL",
        widget=TextArea(),
        render_kw={"rows": 1},
        substitution=True,
    )
    copy_destination = SelectField(
        choices=(
            ("running", "Running"),
            ("candidate", "Candidate"),
            ("startup", "Startup"),
            ("destination_url", "Destination URL"),
        ),
        label="Copy Destination",
        validate_choice=False,
    )
    destination_url = StringField(
        label="Copy destination URL",
        widget=TextArea(),
        render_kw={"rows": 1},
        substitution=True,
    )
    commit_conf = BooleanField(label="Commit")
    xml_conversion = BooleanField(
        label="Convert XML result to dictionary", default=True
    )

    @classmethod
    def form_init(cls):
        parameters = {
            "get_config": ["target", "xml_conversion"],
            "get_filtered_config": [
                "target",
                "xml_filter",
                "xml_conversion",
            ],
            "push_config": [
                "target",
                "xml_filter",
                "default_operation",
                "test_option",
                "error_option",
                "lock",
                "unlock",
                "commit_conf",
                "xml_conversion",
            ],
            "copy_config": [
                "copy_source",
                "source_url",
                "copy_destination",
                "destination_url",
                "commit_conf",
                "xml_conversion",
            ],
            "rpc": ["xml_filter", "xml_conversion"],
        }
        list_parameters = list(set(sum(parameters.values(), [])))
        cls.groups = {
            "NETCONF Parameters": {
                "commands": ["nc_type"] + list_parameters,
                "default": "expanded",
            },
            **ConnectionForm.groups,
        }
        cls.input_data = HiddenField(
            "",
            default=dumps({"fields": list_parameters, "netconf_type": parameters}),
        )
