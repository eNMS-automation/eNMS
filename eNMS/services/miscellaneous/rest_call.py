from requests.auth import HTTPBasicAuth
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.types import JSON

from eNMS import app
from eNMS.database import db
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import (
    BooleanField,
    DictField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
)
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
    username = db.Column(db.SmallString)
    password = db.Column(db.SmallString)

    __mapper_args__ = {"polymorphic_identity": "rest_call_service"}

    def job(self, run, payload, device=None):
        local_variables = locals()
        rest_url = run.sub(run.rest_url, local_variables)
        run.log("info", f"Sending REST Call to {rest_url}", device)
        kwargs = {
            p: run.sub(getattr(self, p), local_variables)
            for p in ("headers", "params", "timeout")
        }
        kwargs["verify"] = run.verify_ssl_certificate
        if self.username:
            kwargs["auth"] = HTTPBasicAuth(
                self.username, app.get_password(self.password)
            )
        if run.call_type in ("POST", "PUT", "PATCH"):
            kwargs["json"] = run.sub(run.payload, local_variables)
        call = getattr(app.request_session, run.call_type.lower())
        response = call(rest_url, **kwargs)
        if response.status_code not in range(200, 300):
            result = {
                "success": False,
                "response_code": response.status_code,
                "response": response.text,
            }
            if response.status_code == 401:
                result["result"] = "Wrong credentials supplied."
            return result
        return {
            "url": rest_url,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "result": response.text,
        }


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
    username = StringField()
    password = PasswordField()
