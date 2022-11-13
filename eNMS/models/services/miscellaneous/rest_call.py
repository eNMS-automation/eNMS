from requests.auth import HTTPBasicAuth
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

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
    payload = db.Column(JSON, default={})
    params = db.Column(JSON, default={})
    headers = db.Column(JSON, default={})
    verify_ssl_certificate = db.Column(Boolean, default=True)
    timeout = db.Column(Integer, default=15)
    credentials = db.Column(db.SmallString, default="custom")
    credential_object_id = db.Column(Integer, ForeignKey("credential.id"))
    credential_object = relationship("Credential")
    custom_username = db.Column(db.SmallString)
    custom_password = db.Column(db.SmallString)

    __mapper_args__ = {"polymorphic_identity": "rest_call_service"}

    def job(self, run, device=None):
        local_variables = locals()
        rest_url = run.sub(run.rest_url, local_variables)
        log_url = run.rest_url if "get_credential" in run.rest_url else rest_url
        run.log("info", f"Sending REST Call to {log_url}", device, logger="security")
        kwargs = {
            parameter: run.sub(getattr(self, parameter), local_variables)
            for parameter in ("headers", "params", "timeout")
        }
        kwargs["verify"] = run.verify_ssl_certificate
        credentials = run.get_credentials(device)
        if self.credentials != "custom" or credentials["username"]:
            kwargs["auth"] = HTTPBasicAuth(
                credentials["username"], credentials["password"]
            )
        if run.call_type in ("POST", "PUT", "PATCH"):
            kwargs["json"] = run.sub(self.payload, local_variables)
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
    payload = DictField(json_only=True, substitution=True)
    params = DictField(substitution=True)
    headers = DictField(substitution=True)
    verify_ssl_certificate = BooleanField("Verify SSL Certificate")
    timeout = IntegerField(default=15)
    credentials = SelectField(
        "Credentials",
        choices=(
            ("device", "Device Credentials"),
            ("credential", "Credential Object"),
            ("user", "User Credentials"),
            ("custom", "Custom Credentials"),
        ),
    )
    credential_object = InstanceField("Credential Object", model="credential")
    custom_username = StringField("Custom Username", substitution=True)
    custom_password = PasswordField("Custom Password", substitution=True)

    def validate(self):
        valid_form = super().validate()
        device_credentials_error = (
            self.credentials.data == "device" and self.run_method.data == "once"
        )
        if device_credentials_error:
            self.credentials.errors.append(
                "Device credentials cannot be selected because the service "
                "'Run Method' is not set to 'Run Once per Device'"
            )
        return valid_form and not device_credentials_error
