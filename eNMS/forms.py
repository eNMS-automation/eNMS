from copy import deepcopy
from datetime import datetime
from flask import request
from flask_login import current_user
from flask_wtf import FlaskForm
from importlib.util import module_from_spec, spec_from_file_location
from os.path import exists
from traceback import format_exc
from wtforms.fields.core import UnboundField
from wtforms.form import FormMeta
from wtforms.validators import InputRequired
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.environment import env
from eNMS.fields import (
    BooleanField,
    HiddenField,
    DictField,
    FloatField,
    InstanceField,
    IntegerField,
    JsonField,
    MultipleInstanceField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
)
from eNMS.variables import vs


class MetaForm(FormMeta):
    def __new__(cls, name, bases, attrs):
        if name == "BaseForm":
            return type.__new__(cls, name, bases, attrs)
        form_type = attrs["form_type"].kwargs["default"]
        form = type.__new__(cls, name, bases, attrs)
        if form.__dict__.get("get_request_allowed", True):
            vs.rbac["get_requests"][f"/{form_type}_form"] = "access"
        if hasattr(form, "form_init"):
            form.form_init()
        if not hasattr(form, "custom_properties"):
            form.custom_properties = {}
        form.custom_properties = {
            **form.custom_properties,
            **vs.properties["custom"].get(form_type, {}),
        }
        for property, values in form.custom_properties.items():
            if not values.get("form", True):
                continue
            if property in vs.private_properties_set:
                field = PasswordField
            else:
                field = {
                    "bool": BooleanField,
                    "dict": DictField,
                    "integer": IntegerField,
                    "json": JsonField,
                    "str": StringField,
                    "select": SelectField,
                    "multiselect": SelectMultipleField,
                }[values.get("type", "str")]
            form_kw = {
                property: values[property]
                for property in ("default", "render_kw", "dont_duplicate")
                if property in values
            }
            form_args = []
            if field in (SelectField, SelectMultipleField):
                form_kw["choices"] = values["choices"]
            if values.get("mandatory", False):
                form_args.append([InputRequired()])
            field = field(values["pretty_name"], *form_args, **form_kw)
            setattr(form, property, field)
            attrs[property] = field
        if form_type in vs.rbac["rbac_models"]:
            form.rbac_properties = vs.rbac["rbac_models"].get(form_type, {})
            setattr(form, "owners", MultipleInstanceField("Owners", model="user"))
            field_properties = {"type": "object-list", "model": "user"}
            vs.form_properties[form_type]["owners"] = field_properties
        for property, property_name in form.rbac_properties.items():
            field = MultipleInstanceField(property_name, model="group")
            setattr(form, property, field)
            field_properties = {"type": "object-list", "model": "group"}
            vs.form_properties[form_type][property] = field_properties
        vs.form_class[form_type] = form
        properties = {}
        for field_name, field in attrs.items():
            if not isinstance(field, UnboundField):
                continue
            field_type = field.kwargs.pop("type", None)
            if not field_type:
                field_type = field.field_class.type
            properties[field_name] = {
                "type": field_type,
                "model": field.kwargs.get("model", None),
                "constraints": field.kwargs.get("constraints", {}),
                "dont_duplicate": field.kwargs.get("dont_duplicate", False),
            }
            if field.args and isinstance(field.args[0], str):
                vs.property_names[field_name] = field.args[0]
            if (
                issubclass(field.field_class, PasswordField)
                and field_name not in vs.private_properties_set
            ):
                vs.private_properties_set.add(field_name)
        vs.form_properties[form_type].update(properties)
        for base in form.__bases__:
            if not hasattr(base, "form_type"):
                continue
            base_form_type = base.form_type.kwargs["default"]
            form.custom_properties.update(base.custom_properties)
            if base_form_type == "service":
                form.service_fields = [
                    property
                    for property in properties
                    if property not in form.custom_properties
                ]
            if getattr(base, "abstract_service", False):
                form.service_fields.extend(vs.form_properties[base_form_type])
            vs.form_properties[form_type].update(vs.form_properties[base_form_type])
        return form

    def __setattr__(self, field, value):
        if hasattr(value, "field_class") and "multiselect" in value.field_class.type:
            form_type = self.form_type.kwargs["default"]
            vs.form_properties[form_type][field] = {"type": value.field_class.type}
        return super().__setattr__(field, value)


class BaseForm(FlaskForm, metaclass=MetaForm):
    rbac_properties = {}

    def form_postprocessing(self, form_data):
        data = {"user": current_user, **form_data.to_dict()}
        if request.files:
            data["file"] = request.files["file"]
        for property, field in vs.form_properties[form_data.get("form_type")].items():
            if field["type"] in ("object-list", "multiselect"):
                value = form_data.getlist(property)
                if field["type"] == "object-list":
                    value = [db.fetch(field["model"], name=name).id for name in value]
                data[property] = value
            elif field["type"] == "object":
                data[property] = form_data.get(property)
            elif field["type"] == "field-list":
                data[property] = []
                for entry in getattr(self, property):
                    properties = entry.data
                    properties.pop("csrf_token")
                    data[property].append(properties)
            elif field["type"] == "bool":
                data[property] = property in form_data
            elif field["type"] in db.field_conversion and property in data:
                data[property] = db.field_conversion[field["type"]](form_data[property])
        return data


class FormFactory:
    def _initialize(self):
        self.generate_instance_insertion_forms()
        self.generate_rbac_forms()
        self.generate_service_forms()
        self.generate_filtering_forms()

    def generate_filtering_forms(self):
        for model in vs.properties["filtering"]:
            if model not in vs.form_class:
                continue
            relations, model_form = {}, vs.form_class[model]
            for related_model, relation in vs.relationships[model].items():
                if hasattr(model_form, related_model):
                    continue
                if related_model in ("edges", "results"):
                    continue
                relations[related_model] = MultipleInstanceField(
                    " ".join(word.capitalize() for word in related_model.split("_")),
                    model=related_model,
                )
                vs.relationships[f"{model}_filtering"][related_model] = relation
            relation_form = {
                "template": "service" if model == "service" else "object",
                "properties": sorted(relations),
                "object_type": model,
                "form_type": HiddenField(default=f"{model}_filtering"),
                **relations,
            }
            type(f"{model}FilteringForm", (model_form,), relation_form)

    def generate_instance_insertion_forms(self):
        for model in ("device", "link", "user", "service"):
            vs.relationships[f"add_{model}s"]["instances"] = {
                "type": "object-list",
                "model": model,
            }
            type(
                f"{model}RelationshipFilteringForm",
                (BaseForm,),
                {
                    "form_type": HiddenField(default=f"add_{model}s"),
                    "action": "eNMS.base.addInstancesToRelation",
                    "model": HiddenField(default=model),
                    "relation_id": HiddenField(),
                    "relation_type": HiddenField(),
                    "property": HiddenField(),
                    "instances": MultipleInstanceField(f"{model}s", model=model),
                    "names": StringField(widget=TextArea(), render_kw={"rows": 8}),
                },
            )

    def generate_rbac_forms(self):
        class GroupForm(RbacForm):
            template = "group"
            form_type = HiddenField(default="group")
            admin_only = BooleanField("Admin Only", default=False)
            force_read_access = BooleanField("Always set 'Read' access", default=False)
            users = MultipleInstanceField("Users", model="user")
            menu = SelectMultipleField("Menu", choices=vs.dualize(vs.rbac["menus"]))
            pages = SelectMultipleField("Pages", choices=vs.dualize(vs.rbac["pages"]))
            get_requests = SelectMultipleField(
                "GET Requests",
                choices=[
                    (key, key)
                    for key, value in vs.rbac["get_requests"].items()
                    if value == "access"
                ],
            )
            post_requests = SelectMultipleField(
                "POST Requests",
                choices=[
                    (key, key)
                    for key, value in vs.rbac["post_requests"].items()
                    if value == "access"
                ],
            )
            delete_requests = SelectMultipleField(
                "DELETE Requests",
                choices=[
                    (key, key)
                    for key, value in vs.rbac["delete_requests"].items()
                    if value == "access"
                ],
            )

            @classmethod
            def form_init(cls):
                cls.pool_properties = []
                for model, properties in vs.rbac["rbac_models"].items():
                    field = SelectMultipleField(choices=list(properties.items()))
                    setattr(cls, f"{model}_access", field)
                    vs.form_properties["group"][f"{model}_access"] = {
                        "type": "multiselect"
                    }
                for property in vs.rbac["rbac_models"]["device"]:
                    property_name = f"rbac_pool_{property}"
                    ui_name = property.split("_")[-1].capitalize()
                    cls.pool_properties.append(property_name)
                    field = MultipleInstanceField(ui_name, model="pool")
                    setattr(cls, property_name, field)
                    field_properties = {"type": "object-list", "model": "pool"}
                    vs.form_properties["group"][property_name] = field_properties

    def generate_service_forms(self):
        for file in (vs.path / "eNMS" / "forms").glob("**/*.py"):
            spec = spec_from_file_location(str(file).split("/")[-1][:-3], str(file))
            spec.loader.exec_module(module_from_spec(spec))

    def register_parameterized_form(self, service_id):
        global_variables = {"form": None, "BaseForm": BaseForm, **vs.form_context}
        indented_form = "\n".join(
            " " * 4 + line
            for line in (
                f"form_type = HiddenField(default='initial-{service_id}')",
                *db.fetch("service", id=service_id).parameterized_form.splitlines(),
            )
        )
        full_form = f"class Form(BaseForm):\n{indented_form}\nform = Form"
        try:
            exec(full_form, global_variables)
            return global_variables["form"]
        except Exception:
            return (
                "<div style='margin: 8px'>The parameterized form could not be  "
                "loaded because of the following error:"
                f"<br><pre>{format_exc()}</pre></div>"
            )


class AddServiceForm(BaseForm):
    form_type = HiddenField(default="add_services_to_workflow")
    template = "add_services_to_workflow"
    mode = SelectField(
        "Mode",
        choices=(
            ("deep", "Deep Copy (creates a duplicate from the service)"),
            ("shallow", "Shallow Copy (creates a reference to the service)"),
        ),
    )
    search = StringField()


class AddToNetworkForm(BaseForm):
    action = "eNMS.networkBuilder.addObjectsToNetwork"
    form_type = HiddenField(default="add_to_network")
    nodes = MultipleInstanceField("Nodes", model="node")
    add_connected_links = BooleanField("Add connected links", default=False)
    links = MultipleInstanceField("Links", model="link")
    add_connected_nodes = BooleanField("Add connected nodes", default=False)
    pools = MultipleInstanceField("Pools", model="pool")


class AdminForm(BaseForm):
    template = "administration"
    form_type = HiddenField(default="administration")


class ChangelogForm(BaseForm):
    form_type = HiddenField(default="changelog")
    id = HiddenField()
    severity = SelectField(
        "Severity",
        choices=(
            ("debug", "Debug"),
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
            ("critical", "Critical"),
        ),
    )
    content = StringField(widget=TextArea(), render_kw={"rows": 20})


class CredentialForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="credential")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    creator = StringField(render_kw={"readonly": True})
    admin_only = BooleanField("Admin Only", default=False)
    description = StringField(widget=TextArea(), render_kw={"rows": 6})
    role = SelectField(
        "Role",
        choices=(
            ("read-write", "Read Write"),
            ("read-only", "Read Only"),
        ),
    )
    subtype = SelectField(
        "Subtype",
        choices=(("password", "Username / Password"), ("key", "SSH Key")),
    )
    device_pools = MultipleInstanceField("Devices", model="pool")
    groups = MultipleInstanceField("Groups", model="group")
    priority = IntegerField("Priority", default=1)
    username = StringField("Username")
    password = PasswordField("Password")
    private_key = StringField(widget=TextArea(), render_kw={"rows": 1})
    enable_password = PasswordField("'Enable' Password")

    def validate(self, **_):
        valid_form = super().validate()
        invalid_priority = not current_user.is_admin and self.priority.data > 1
        if invalid_priority:
            self.priority.errors.append(
                "Non admin users cannot set a priority higher than 1."
            )
        return valid_form and not invalid_priority


class DatabaseDeletionForm(BaseForm):
    action = "eNMS.administration.databaseDeletion"
    form_type = HiddenField(default="database_deletion")
    deletion_choices = vs.dualize(db.import_export_models)
    deletion_types = SelectMultipleField(
        "Instances to delete", choices=deletion_choices
    )


class DatabaseMigrationsForm(BaseForm):
    template = "database_migration"
    form_type = HiddenField(default="database_migration")
    empty_database_before_import = BooleanField("Empty Database before Import")
    skip_pool_update = BooleanField(
        "Skip the Pool update after Import", default="checked"
    )
    export_private_properties = BooleanField(
        "Include private properties", default="checked"
    )
    export_choices = vs.dualize(db.import_export_models)
    import_export_types = SelectMultipleField(
        "Instances to migrate", choices=export_choices
    )


class DebugForm(BaseForm):
    template = "debug"
    form_type = HiddenField(default="debug")
    snippets = SelectField(choices=(), validate_choice=False)
    code = StringField(
        "Python Code",
        type="code",
        python=True,
        widget=TextArea(),
        render_kw={"rows": 15},
    )
    output = StringField("Output", widget=TextArea(), render_kw={"rows": 16})


class DeviceConnectionForm(BaseForm):
    template = "device_connection"
    form_type = HiddenField(default="device_connection")
    address_choices = [("ip_address", "IP address"), ("name", "Name")] + [
        (property, values["pretty_name"])
        for property, values in vs.properties["custom"]["device"].items()
        if values.get("is_address", False)
    ]
    address = SelectField(choices=address_choices)
    username = StringField("Username")
    password = PasswordField("Password")


class DeviceDataForm(BaseForm):
    template = "device_data"
    form_type = HiddenField(default="device_data")
    data_type = SelectField("Display", choices=vs.configuration_properties)


class ExcelExportForm(BaseForm):
    action = "eNMS.inventory.exportTopology"
    form_type = HiddenField(default="excel_export")
    export_filename = StringField("Filename")


class ExcelImportForm(BaseForm):
    template = "topology_import"
    form_type = HiddenField(default="excel_import")
    replace = BooleanField("Replace Existing Topology")


class FileForm(BaseForm):
    form_type = HiddenField(default="file")
    id = HiddenField()
    path = StringField("Path", [InputRequired()])
    description = StringField(widget=TextArea(), render_kw={"rows": 8})
    filename = StringField("Filename", render_kw={"readonly": True})
    name = StringField("Name", render_kw={"readonly": True})
    last_modified = StringField("Last Modified", render_kw={"readonly": True})
    last_updated = StringField("Last Updated", render_kw={"readonly": True})
    status = StringField("Status", render_kw={"readonly": True})

    def validate(self, **_):
        valid_form = super().validate()
        current_file = db.fetch("file", id=self.id.data, allow_none=True)
        path_taken = exists(self.path.data)
        change_of_path = current_file and self.path.data != current_file.path
        path_already_used = (not current_file or change_of_path) and path_taken
        if path_already_used:
            self.path.errors.append("There is already a file at the specified path.")
        out_of_scope_path = not self.path.data.startswith(env.file_path)
        if out_of_scope_path:
            self.path.errors.append(
                f"The path must be in the {env.file_path} directory."
            )
        return valid_form and not any([path_already_used, out_of_scope_path])


class FolderForm(FileForm):
    form_type = HiddenField(default="folder")


class FileEditorForm(BaseForm):
    template = "file_editor"
    form_type = HiddenField(default="file_editor")
    file_content = StringField(widget=TextArea(), render_kw={"rows": 8})


class ImportServices(BaseForm):
    action = "eNMS.automation.importServices"
    template = "upload_services"
    form_type = HiddenField(default="import_services")


class LoginForm(BaseForm):
    form_type = HiddenField(default="login")
    get_request_allowed = False
    authentication_method = SelectField(
        "Authentication Method",
        choices=[
            (method, properties["display_name"])
            for method, properties in vs.settings["authentication"]["methods"].items()
            if properties["enabled"]
        ],
    )
    username = StringField("Name", [InputRequired()])
    password = PasswordField("Password", [InputRequired()])


class ObjectForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="object")
    get_request_allowed = False
    id = HiddenField()
    name = StringField("Name")
    creator = StringField(render_kw={"readonly": True})
    type = StringField("Type")
    description = StringField("Description")
    subtype = StringField("Subtype")
    location = StringField("Location")


class PoolForm(BaseForm):
    template = "pool"
    models = ("device", "link")
    form_type = HiddenField(default="pool")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    creator = StringField(render_kw={"readonly": True})
    admin_only = BooleanField("Pool visible to admin users only")
    description = StringField(widget=TextArea(), render_kw={"rows": 8})
    manually_defined = BooleanField("Manually defined (won't be automatically updated)")

    @classmethod
    def form_init(cls):
        for model in cls.models:
            setattr(cls, f"{model}_properties", vs.properties["filtering"][model])
            for property in vs.properties["filtering"][model]:
                setattr(cls, f"{model}_{property}", StringField(property))
                setattr(cls, f"{model}_{property}_invert", BooleanField(property))
                vs.form_properties["pool"][f"{model}_{property}_match"] = {
                    "type": "list"
                }
                vs.form_properties["pool"][f"{model}_{property}_invert"] = {
                    "type": "bool"
                }
                setattr(
                    cls,
                    f"{model}_{property}_match",
                    SelectField(
                        choices=(
                            ("inclusion", "Inclusion"),
                            ("equality", "Equality"),
                            ("regex", "Regular Expression"),
                            ("empty", "Empty"),
                        )
                    ),
                )


class RbacForm(BaseForm):
    form_type = HiddenField(default="rbac")
    get_request_allowed = False
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    creator = StringField(render_kw={"readonly": True})
    description = StringField(widget=TextArea(), render_kw={"rows": 6})
    email = StringField("Email")


class RestartWorkflowForm(BaseForm):
    action = "eNMS.workflowBuilder.restartWorkflow"
    form_type = HiddenField(default="restart_workflow")
    start_services = HiddenField()
    restart_runtime = SelectField(
        "Restart Runtime", [InputRequired()], choices=(), validate_choice=False
    )
    targets = SelectField(
        "Targets",
        choices=(
            ("Manually defined", "Use the Devices and Pools manually defined below."),
            ("Restart run", "Use the Targets from the Restart Runtime selected above."),
            ("Workflow", "Use the Targets selected in the parent Workflow"),
        ),
    )
    restart_devices = MultipleInstanceField("Devices", model="device")
    restart_pools = MultipleInstanceField("Pools", model="pool")


class ResultLogDeletionForm(BaseForm):
    action = "eNMS.administration.resultLogDeletion"
    form_type = HiddenField(default="result_log_deletion")
    deletion_types = SelectMultipleField(
        "Instances do delete",
        choices=[("run", "result"), ("changelog", "changelog")],
    )
    date_time = StringField(type="date", label="Delete Records before")


class RunForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="run")
    id = HiddenField()
    name = StringField("Name")
    service_name = StringField("Service Name")
    runtime = StringField("Runtime")
    duration = StringField("Duration")
    creator = StringField("Creator")
    status = StringField("Status")
    trigger = StringField("Trigger")
    parameterized_run = BooleanField("Parameterized Run")
    labels = StringField("Labels")


class RunServiceForm(BaseForm):
    action = "eNMS.automation.runServicesOnTargets"
    button_label = "Run Service"
    button_class = "primary"
    form_type = HiddenField(default="run_service")
    targets = HiddenField()
    type = HiddenField()
    service = InstanceField("Services", model="service")


class ServerForm(BaseForm):
    form_type = HiddenField(default="server")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    creator = StringField(render_kw={"readonly": True})
    description = StringField(widget=TextArea(), render_kw={"rows": 6})
    ip_address = StringField("IP address")
    weight = IntegerField("Weight", default=1)


class ServiceForm(BaseForm):
    template = "service"
    form_type = HiddenField(default="service")
    get_request_allowed = False
    id = HiddenField()
    name = StringField("Name", help="common/full_name", ui_name="Full Name")
    creator = StringField(render_kw={"readonly": True})
    type = StringField("Service Type")
    shared = BooleanField("Shared", help="common/shared")
    scoped_name = StringField("Scoped Name", [InputRequired()], ui_name="Name")
    description = StringField("Description")
    device_query = StringField(
        "Device Query",
        python=True,
        widget=TextArea(),
        render_kw={"rows": 2},
        help="common/device_query",
        ui_name="Device Query (define targets from a python query)",
    )
    device_query_property = SelectField(
        "Query Property Type",
        choices=(("name", "Name"), ("ip_address", "IP address")),
        no_search=True,
    )
    disabled = BooleanField("Disabled")
    disabled_info = StringField("Disabled Time & User", render_kw={"readonly": True})
    restrict_to_owners = SelectMultipleField(
        "Restrict to Owners", choices=(("edit", "Edit"), ("run", "Run")), no_search=True
    )
    target_devices = MultipleInstanceField("Devices", model="device")
    disable_result_creation = BooleanField("Save only failed results")
    target_pools = MultipleInstanceField("Pools", model="pool")
    update_target_pools = BooleanField("Update target pools before running")
    update_pools_after_running = BooleanField("Update pools after running")
    workflows = MultipleInstanceField("Workflows", model="workflow")
    waiting_time = IntegerField(
        "Time to Wait before next service is started (in seconds)", default=0
    )
    priority = IntegerField("Priority", default=10, help="common/priority")
    report_template = SelectField("Report Template", choices=(vs.dualize(vs.reports)))
    report = StringField(widget=TextArea(), render_kw={"rows": 8}, substitution=True)
    report_format = SelectField(
        "Report Display Format",
        choices=(("text", "Text"), ("html", "HTML")),
        no_search=True,
    )
    report_jinja2_template = BooleanField("Interpret Report as Jinja2 Template")
    display_report = BooleanField("Display Report instead of Results")
    email_report = BooleanField("Send Report in Mail Notification")
    send_notification = BooleanField("Send a notification")
    send_notification_method = SelectField(
        "Notification Method",
        choices=(("mail", "Mail"), ("slack", "Slack"), ("mattermost", "Mattermost")),
        no_search=True,
    )
    notification_header = StringField(
        widget=TextArea(),
        render_kw={"rows": 8},
        substitution=True,
        help="common/notification_header",
    )
    include_device_results = BooleanField("Include Device Results")
    include_link_in_summary = BooleanField("Include Result Link in Summary")
    display_only_failed_nodes = BooleanField("Display only Failed Devices")
    mail_recipient = StringField(
        "Mail Recipients (separated by comma)", substitution=True
    )
    reply_to = StringField("Reply-to Email Address")
    number_of_retries = IntegerField(
        "Number of retries", default=0, help="common/number_of_retries"
    )
    time_between_retries = IntegerField("Time between retries (in seconds)", default=10)
    max_number_of_retries = IntegerField("Maximum number of retries", default=100)
    credential_type = SelectField(
        "Type of Credentials",
        choices=(
            ("any", "Any"),
            ("read-write", "Read Write"),
            ("read-only", "Read Only"),
        ),
        help="common/type_of_credentials",
        no_search=True,
    )
    maximum_runs = IntegerField("Maximum number of runs", default=1)
    skip_query = StringField(
        "Skip Query (Python)",
        python=True,
        widget=TextArea(),
        render_kw={"rows": 2},
        help="common/skip_query",
    )
    skip_value = SelectField(
        "Skip Value",
        choices=(
            ("success", "Success"),
            ("failure", "Failure"),
            ("discard", "Discard"),
        ),
        help="common/skip_value",
        no_search=True,
    )
    vendor = SelectField(
        "Vendor",
        choices=vs.dualize(vs.properties["property_list"]["service"]["vendor"]),
        validate_choice=False,
    )
    operating_system = SelectField(
        "Operating System",
        choices=vs.dualize(
            vs.properties["property_list"]["service"]["operating_system"]
        ),
        validate_choice=False,
    )
    iteration_values = StringField(
        "Iteration Values", python=True, help="common/iteration_values"
    )
    initial_payload = DictField(help="common/initial_payload")
    mandatory_parametrization = BooleanField(
        "Parameterized Form is Mandatory", help="common/mandatory_parametrization"
    )
    parameterized_form = StringField(
        type="code",
        python=True,
        widget=TextArea(),
        default="\n".join(vs.automation["parameterized_form"]),
        help="common/parameterized_form",
    )
    iteration_variable_name = StringField(
        "Iteration Variable Name", default="iteration_value"
    )
    iteration_devices = StringField(
        "Iteration Devices", python=True, help="common/iteration_devices"
    )
    iteration_devices_property = SelectField(
        "Iteration Devices Property",
        choices=(("name", "Name"), ("ip_address", "IP address")),
        no_search=True,
    )
    preprocessing = StringField(
        type="code", python=True, widget=TextArea(), help="common/preprocessing"
    )
    postprocessing = StringField(
        type="code", python=True, widget=TextArea(), help="common/postprocessing"
    )
    postprocessing_mode = SelectField(
        choices=(
            ("success", "Run on success only"),
            ("failure", "Run on failure only"),
            ("always", "Always run"),
        ),
        no_search=True,
    )
    admin_only = BooleanField("Admin Only", default=False)
    log_level = SelectField(
        "Logging",
        choices=(*enumerate(vs.log_levels), (-1, "Disable logging")),
        default=1,
        help="common/logging",
        no_search=True,
    )
    multiprocessing = BooleanField("Multiprocessing", help="common/multiprocessing")
    max_processes = IntegerField("Maximum number of processes", default=15)
    validation_condition = SelectField(
        choices=(
            ("none", "No validation"),
            ("success", "Run on success only"),
            ("failure", "Run on failure only"),
            ("always", "Always run"),
        ),
        no_search=True,
    )
    conversion_method = SelectField(
        choices=(
            ("none", "No conversion"),
            ("text", "Text"),
            ("json", "Json dictionary"),
            ("xml", "XML dictionary"),
        ),
        no_search=True,
    )
    validation_method = SelectField(
        "Validation Method",
        choices=(
            ("text", "Validation by text match"),
            ("dict_included", "Validation by dictionary inclusion"),
            ("dict_equal", "Validation by dictionary equality"),
        ),
        no_search=True,
    )
    validation_section = StringField("Section to Validate", default="results['result']")
    content_match = StringField(
        "Content Match", widget=TextArea(), render_kw={"rows": 8}, substitution=True
    )
    content_match_regex = BooleanField('"Content Match" is a regular expression')
    dict_match = DictField("Dictionary to Match Against", substitution=True)
    negative_logic = BooleanField("Negative logic")
    delete_spaces_before_matching = BooleanField("Delete Spaces before Matching")
    run_method = SelectField(
        "Run Method",
        choices=(
            ("per_device", "Run the service once per device"),
            ("once", "Run the service once"),
        ),
        no_search=True,
    )
    group_properties = {
        "step1-1": [
            "name",
            "scoped_name",
            "creator",
            "admin_only",
            "type",
            "disabled",
            "disabled_info",
            "shared",
            "workflows",
            "description",
            "vendor",
            "operating_system",
            "initial_payload",
            "mandatory_parametrization",
            "parameterized_form",
            "priority",
            "number_of_retries",
            "time_between_retries",
            "max_number_of_retries",
            "credential_type",
            "log_level",
            "disable_result_creation",
            "update_pools_after_running",
        ],
        "step1-2": [
            "preprocessing",
            "skip_query",
            "skip_value",
            "maximum_runs",
            "waiting_time",
        ],
        "step3-1": [
            "run_method",
            "target_devices",
            "target_pools",
            "update_target_pools",
            "device_query",
            "device_query_property",
            "multiprocessing",
            "max_processes",
        ],
        "step3-2": [
            "iteration_devices",
            "iteration_devices_property",
            "iteration_values",
            "iteration_variable_name",
        ],
        "step4-1": [
            "conversion_method",
            "postprocessing_mode",
            "postprocessing",
        ],
        "step4-2": [
            "validation_condition",
            "validation_method",
            "validation_section",
            "content_match",
            "content_match_regex",
            "dict_match",
            "delete_spaces_before_matching",
            "negative_logic",
        ],
        "step4-3": [
            "report_template",
            "report_format",
            "report_jinja2_template",
            "report",
            "display_report",
            "email_report",
        ],
        "step4-4": [
            "send_notification",
            "send_notification_method",
            "notification_header",
            "include_device_results",
            "include_link_in_summary",
            "mail_recipient",
            "reply_to",
            "display_only_failed_nodes",
        ],
    }

    def validate(self, **_):
        valid_form = super().validate()
        no_recipient_error = (
            self.send_notification.data
            and self.send_notification_method.data == "mail"
            and not self.mail_recipient.data
        )
        if no_recipient_error:
            self.mail_recipient.errors.append(
                "Please add at least one recipient for the mail notification."
            )
        forbidden_name_error = self.scoped_name.data in ("Start", "End", "Placeholder")
        if forbidden_name_error:
            self.name.errors.append("This name is not allowed.")
        conversion_validation_mismatch = self.validation_condition.data != "none" and (
            self.conversion_method.data == "text"
            and "dict" in self.validation_method.data
            or self.conversion_method.data in ("xml", "json")
            and "dict" not in self.validation_method.data
        )
        if conversion_validation_mismatch:
            self.conversion_method.errors.append(
                f"The conversion method is set to {self.conversion_method.data}"
                f" and the validation method to {self.validation_method.data} :"
                " these do not match."
            )
        empty_validation = self.validation_condition.data != "none" and (
            self.validation_method.data == "text"
            and not self.content_match.data
            or self.validation_method.data == "dict_included"
            and self.dict_match.data == "{}"
        )
        if empty_validation:
            self.content_match.errors.append(
                f"The validation method is set to '{self.validation_method.data}'"
                f" and the matching value is empty: these do no match."
            )
        too_many_threads_error = (
            self.max_processes.data > vs.settings["automation"]["max_process"]
        )
        if too_many_threads_error:
            self.max_processes.errors.append(
                "The number of threads used for multiprocessing must be "
                f"less than {vs.settings['automation']['max_process']}."
            )
        shared_service_error = not self.shared.data and len(self.workflows.data) > 1
        if shared_service_error:
            self.shared.errors.append(
                "The 'shared' property is unticked, but the service belongs"
                " to more than one workflow: this is incompatible."
            )
        return (
            valid_form
            and not conversion_validation_mismatch
            and not empty_validation
            and not forbidden_name_error
            and not no_recipient_error
            and not shared_service_error
            and not too_many_threads_error
        )


class TaskForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="task")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    creator = StringField(render_kw={"readonly": True})
    admin_only = BooleanField("Admin Only", default=False)
    scheduling_mode = SelectField(
        "Scheduling Mode",
        choices=(("cron", "Crontab Scheduling"), ("standard", "Standard Scheduling")),
    )
    description = StringField("Description")
    start_date = StringField("Start Date", type="date")
    end_date = StringField("End Date", type="date")
    frequency = IntegerField("Frequency", default=0)
    frequency_unit = SelectField(
        "Frequency Unit",
        choices=(
            ("seconds", "Seconds"),
            ("minutes", "Minutes"),
            ("hours", "Hours"),
            ("days", "Days"),
        ),
    )
    crontab_expression = StringField("Crontab Expression")
    initial_payload = DictField("Payload")
    devices = MultipleInstanceField("Devices", model="device")
    pools = MultipleInstanceField("Pools", model="pool")
    service = InstanceField("Service", model="service")

    def validate(self, **_):
        valid_form = super().validate()
        if self.name.data == "Bulk Edit":
            return valid_form
        no_date = self.scheduling_mode.data == "standard" and not self.start_date.data
        if no_date:
            self.start_date.errors.append("A start date must be set.")
        invalid_end_date = self.end_date.data and datetime.strptime(
            self.end_date.data, "%d/%m/%Y %H:%M:%S"
        ) <= datetime.strptime(self.start_date.data, "%d/%m/%Y %H:%M:%S")
        if invalid_end_date:
            self.end_date.errors.append("The end date must come after the start date.")
        invalid_frequency = (
            self.end_date.data
            and not self.frequency.data
            and self.scheduling_mode.data == "standard"
        )
        if invalid_frequency:
            self.frequency.errors.append("A periodic task must have a frequency.")
        no_cron_expression = (
            self.scheduling_mode.data == "cron" and not self.crontab_expression.data
        )
        if no_cron_expression:
            self.crontab_expression.errors.append("A crontab expression must be set.")
        no_service = not self.service.data
        if no_service:
            self.service.errors.append("No service set.")
        return valid_form and not any(
            [
                no_date,
                no_cron_expression,
                no_service,
                invalid_end_date,
                invalid_frequency,
            ]
        )


class UploadFilesForm(BaseForm):
    template = "upload_files"
    folder = HiddenField()
    form_type = HiddenField(default="upload_files")


class UserProfileForm(BaseForm):
    form_type = HiddenField(default="profile")
    action = "eNMS.administration.saveProfile"
    name = StringField("Name")
    email = StringField("Email")
    landing_page = SelectField("Landing Page", validate_choice=False)
    theme = SelectField(
        "Theme",
        choices=[
            (theme, values["name"]) for theme, values in vs.themes["themes"].items()
        ],
    )
    password = PasswordField("Password")

    def validate(self, **_):
        valid_form = super().validate()
        invalid_password = self.password.data and (
            not vs.settings["authentication"]["allow_password_change"]
            or current_user.authentication != "database"
        )
        if invalid_password:
            self.password.errors.append("Changing user password is not allowed.")
        return valid_form and not invalid_password


class WorkflowLabelForm(BaseForm):
    form_type = HiddenField(default="label")
    action = "eNMS.builder.createLabel"
    text = StringField(widget=TextArea(), render_kw={"rows": 15})
    size = IntegerField("Font Size", default=14)
    alignment = SelectField(
        "Text Alignment",
        choices=(("left", "Left"), ("center", "Center"), ("right", "Right")),
    )


class WorkflowEdgeForm(BaseForm):
    form_type = HiddenField(default="workflow_edge")
    id = HiddenField()
    label = StringField()
    color = StringField()


class ConnectionForm(ServiceForm):
    form_type = HiddenField(default="connection")
    get_request_allowed = False
    abstract_service = True
    credentials = SelectField(
        "Credentials",
        choices=(
            ("device", "Device Credentials"),
            ("object", "Named Credential"),
            ("custom", "Custom Credentials"),
        ),
    )
    named_credential = InstanceField("Named Credential", model="credential")
    custom_username = StringField("Custom Username", substitution=True)
    custom_password = PasswordField("Custom Password", substitution=True)
    start_new_connection = BooleanField("Start New Connection")
    connection_name = StringField("Connection Name", default="default")
    close_connection = BooleanField("Close Connection")
    groups = {
        "Connection Parameters": {
            "commands": [
                "credentials",
                "named_credential",
                "custom_username",
                "custom_password",
                "start_new_connection",
                "connection_name",
                "close_connection",
            ],
            "default": "expanded",
        }
    }


class DeviceForm(ObjectForm):
    form_type = HiddenField(default="device")
    icon = SelectField(
        "Icon", choices=list(vs.visualization["icons"].items()), default="router"
    )
    ip_address = StringField("IP address")
    port = IntegerField("Port", default=22)
    vendor = SelectField(
        "Vendor",
        choices=vs.dualize(vs.properties["property_list"]["device"]["vendor"]),
    )
    model = SelectField(
        "Model",
        choices=vs.dualize(vs.properties["property_list"]["device"]["model"]),
    )
    operating_system = SelectField(
        "Operating System",
        choices=vs.dualize(
            vs.properties["property_list"]["device"]["operating_system"]
        ),
    )
    os_version = StringField("OS Version")
    latitude = StringField("Latitude", default=0.0)
    longitude = StringField("Longitude", default=0.0)
    napalm_driver = SelectField(
        "NAPALM Driver", choices=vs.napalm_drivers, default="ios"
    )
    netmiko_driver = SelectField(
        "Netmiko Driver", choices=vs.netmiko_drivers, default="cisco_ios"
    )
    scrapli_driver = SelectField(
        "Scrapli Driver", choices=vs.scrapli_drivers, default="cisco_iosxe"
    )
    netconf_driver = SelectField(
        "Netconf Driver", choices=vs.netconf_drivers, default="default"
    )
    gateways = MultipleInstanceField("Gateways", model="gateway")


class LinkForm(ObjectForm):
    form_type = HiddenField(default="link")
    vendor = SelectField(
        "Vendor",
        choices=vs.dualize(vs.properties["property_list"]["link"]["vendor"]),
    )
    model = SelectField(
        "Model",
        choices=vs.dualize(vs.properties["property_list"]["link"]["model"]),
    )
    source = InstanceField("Source", model="device")
    destination = InstanceField("Destination", model="device")
    color = StringField("Color")


class NapalmForm(ConnectionForm):
    form_type = HiddenField(default="napalm")
    get_request_allowed = False
    abstract_service = True
    driver = SelectField(
        choices=[("device", "Use Device Driver"), *vs.napalm_drivers],
    )
    timeout = IntegerField(default=10)
    optional_args = DictField()
    groups = {
        "Napalm Parameters": {
            "commands": ["driver", "timeout", "optional_args"],
            "default": "expanded",
        },
        **ConnectionForm.groups,
    }


class ParametersForm(BaseForm):
    form_type = HiddenField(default="parameters")
    id = HiddenField()
    banner_active = BooleanField()
    banner_deactivate_on_restart = BooleanField()
    banner_properties = JsonField()


class NetmikoForm(ConnectionForm):
    form_type = HiddenField(default="netmiko")
    abstract_service = True
    driver = SelectField(
        choices=[("device", "Use Device Driver"), *vs.netmiko_drivers],
    )
    enable_mode = BooleanField(
        "Enable mode (run in enable mode or as root)", default=True
    )
    config_mode = BooleanField(
        "Config mode (See Advanced Parameters to override the config mode command)",
        default=False,
    )
    fast_cli = BooleanField()
    timeout = FloatField(default=10.0)
    delay_factor = FloatField(
        (
            "Delay Factor (Changing from default of 1"
            " will nullify Netmiko Timeout setting)"
        ),
        default=1.0,
    )
    global_delay_factor = FloatField(
        (
            "Global Delay Factor (Changing from default of 1"
            " will nullify Netmiko Timeout setting)"
        ),
        default=1.0,
    )
    jump_on_connect = BooleanField(
        "Jump to remote device on connect",
        default=False,
        help="netmiko/jump_on_connect",
    )
    jump_command = StringField(
        label="Command that jumps to device",
        default="ssh jump_server_IP",
        substitution=True,
        help="netmiko/jump_command",
    )
    jump_username = StringField(
        label="Device username", substitution=True, help="netmiko/jump_username"
    )
    jump_password = PasswordField(
        label="Device password", substitution=True, help="netmiko/jump_password"
    )
    exit_command = StringField(
        label="Command to exit device back to original device",
        default="exit",
        substitution=True,
        help="netmiko/exit_command",
    )
    expect_username_prompt = StringField(
        "Expected username prompt",
        default="username:",
        substitution=True,
        help="netmiko/expect_username_prompt",
    )
    expect_password_prompt = StringField(
        "Expected password prompt",
        default="password",
        substitution=True,
        help="netmiko/expect_password_prompt",
    )
    expect_prompt = StringField(
        "Expected prompt after login",
        default="admin.*$",
        substitution=True,
        help="netmiko/expect_prompt",
    )
    groups = {
        "Netmiko Parameters": {
            "commands": [
                "driver",
                "enable_mode",
                "config_mode",
                "fast_cli",
                "timeout",
                "delay_factor",
                "global_delay_factor",
            ],
            "default": "expanded",
        },
        **ConnectionForm.groups,
        "Jump on connect Parameters": {
            "commands": [
                "jump_on_connect",
                "jump_command",
                "expect_username_prompt",
                "jump_username",
                "expect_password_prompt",
                "jump_password",
                "expect_prompt",
                "exit_command",
            ],
            "default": "hidden",
        },
    }

    def validate(self, **_):
        valid_form = super().validate()
        if not hasattr(self, "auto_find_prompt") or not hasattr(self, "expect_string"):
            return valid_form
        invalid_prompt_configuration = (
            self.auto_find_prompt.data
            and self.expect_string.data
            or not self.auto_find_prompt.data
            and not self.expect_string.data
        )
        if invalid_prompt_configuration:
            self.auto_find_prompt.errors.append(
                "'Auto Find Prompt' and 'Expect String' are mutually exclusive:"
                "If 'Auto Find Prompt' is checked, 'Expect String' must be empty, "
                "and if it is unchecked, 'Expect String' cannot be left empty."
            )
        return valid_form and not invalid_prompt_configuration


class ScrapliForm(ConnectionForm):
    form_type = HiddenField(default="scrapli")
    abstract_service = True
    driver = SelectField(
        choices=[("device", "Use Device Driver"), *vs.scrapli_drivers],
    )
    is_configuration = BooleanField()
    transport = SelectField(choices=vs.dualize(("system", "paramiko", "ssh2")))
    timeout_socket = FloatField("Socket Timeout", default=15.0)
    timeout_transport = FloatField("Transport Timeout", default=30.0)
    timeout_ops = FloatField("Ops Timeout", default=30.0)
    groups = {
        "Scrapli Parameters": {
            "commands": [
                "driver",
                "is_configuration",
                "transport",
                "timeout_socket",
                "timeout_transport",
                "timeout_ops",
            ],
            "default": "expanded",
        },
        **ConnectionForm.groups,
    }


class UserForm(RbacForm):
    form_type = HiddenField(default="user")
    groups = MultipleInstanceField("Groups", model="group")
    theme = SelectField(
        "Theme",
        choices=[
            (theme, values["name"]) for theme, values in vs.themes["themes"].items()
        ],
    )
    authentication = SelectField(
        "Authentication",
        choices=[
            (method, values["display_name"])
            for method, values in vs.settings["authentication"]["methods"].items()
        ],
    )
    password = PasswordField("Password")
    is_admin = BooleanField(default=False)


class ReplacementForm(FlaskForm):
    pattern = StringField("Pattern")
    replace_with = StringField("Replace With")


class CommandsForm(FlaskForm):
    value = StringField("Command")
    prefix = StringField("Label")


form_factory = FormFactory()
