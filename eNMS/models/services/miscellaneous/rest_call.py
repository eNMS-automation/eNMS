from ast import literal_eval
from json import loads
from requests.auth import HTTPBasicAuth
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.environment import env
from eNMS.fields import (
    BooleanField,
    DictField,
    HiddenField,
    InstanceField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
)
from eNMS.forms import ServiceForm
from eNMS.models.automation import Service


class RestCallService(Service):
    __tablename__ = "rest_call_service"
    pretty_name = "REST Call"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    call_type = db.Column(db.SmallString)
    rest_url = db.Column(db.LargeString)
    payload = db.Column(db.LargeString)
    substitution_type = db.Column(db.SmallString)
    params = db.Column(JSON, default={})
    headers = db.Column(JSON, default={})
    proxies = db.Column(JSON, default={})
    verify_ssl_certificate = db.Column(Boolean, default=True)
    allow_redirects = db.Column(Boolean, default=True)
    timeout = db.Column(Integer, default=15)
    credentials = db.Column(db.SmallString, default="custom")
    named_credential_id = db.Column(
        Integer, ForeignKey("credential.id", ondelete="SET NULL")
    )
    named_credential = relationship("Credential")
    custom_username = db.Column(db.SmallString)
    custom_password = db.Column(db.SmallString)

    __mapper_args__ = {"polymorphic_identity": "rest_call_service"}

    @staticmethod
    def job(self, run, device=None):
        local_variables = locals()
        rest_url = run.sub(run.rest_url, local_variables)
        log_url = run.safe_log(run.rest_url, rest_url)
        run.log("info", f"Sending REST Call to {log_url}", device, logger="security")
        kwargs = {
            parameter: run.sub(getattr(self, parameter), local_variables)
            for parameter in ("headers", "params", "proxies", "timeout")
        }
        kwargs["verify"] = run.verify_ssl_certificate
        kwargs["allow_redirects"] = run.allow_redirects
        if run.call_type in ("POST", "PUT", "PATCH"):
            if run.substitution_type == "str":
                kwargs["json"] = literal_eval(run.sub(self.payload, local_variables))
            else:
                kwargs["json"] = run.sub(loads(self.payload), local_variables)
        if run.dry_run:
            return {"url": log_url, "kwargs": kwargs}
        credentials = run.get_credentials(device, add_secret=False)
        if self.credentials != "custom" or credentials["username"]:
            kwargs["auth"] = HTTPBasicAuth(
                credentials["username"], credentials["password"]
            )
        call = getattr(env.request_session, run.call_type.lower())
        response = call(rest_url, **kwargs)
        result = {
            "url": log_url,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "result": response.text,
        }
        if response.status_code not in range(200, 300):
            result["success"] = False
        return result


class RestCallForm(ServiceForm):
    form_type = HiddenField(default="rest_call_service")
    call_type = SelectField(
        choices=(
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("DELETE", "DELETE"),
            ("PATCH", "PATCH"),
        )
    )
    rest_url = StringField(substitution=True)
    payload = StringField(substitution=True, widget=TextArea(), render_kw={"rows": 6})
    substitution_type = SelectField(
        "Payload Substitution Type",
        choices=(
            ("str", "String Substitution"),
            ("dict", "Dict Substitution"),
        ),
    )
    params = DictField(substitution=True)
    headers = DictField(substitution=True)
    proxies = DictField(substitution=True)
    verify_ssl_certificate = BooleanField("Verify SSL Certificate")
    allow_redirects = BooleanField("Allow Redirects", default=True)
    timeout = IntegerField(default=15)
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

    def validate(self, **_):
        valid_form = super().validate()
        device_credentials_error = (
            self.credentials.data == "device" and self.run_method.data == "once"
        )
        if device_credentials_error:
            self.credentials.errors.append(
                "Device credentials cannot be selected because the service "
                "'Run Method' is not set to 'Run Once per Device'"
            )
        invalid_json = False
        if self.substitution_type.data == "dict":
            try:
                loads(self.payload.data)
            except Exception:
                invalid_json = True
        if invalid_json:
            self.payload.errors.append(
                "The 'Substitution Type' property is set to 'Dict Substitution',"
                " but the payload is not valid JSON object"
            )
        return valid_form and not device_credentials_error and not invalid_json
