from json import dumps
from requests import (
    get as rest_get,
    post as rest_post,
    put as rest_put,
    delete as rest_delete,
    patch as rest_patch,
)
from requests.auth import HTTPBasicAuth
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.types import JSON
from typing import Optional
from wtforms import (
    BooleanField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
)

from eNMS.database.dialect import Column, LargeString, MutableDict, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import (
    DictSubstitutionField,
    JsonSubstitutionField,
    SubstitutionField,
)
from eNMS.forms.services import ValidationForm
from eNMS.models.automation import Service
from eNMS.models.execution import Run
from eNMS.models.inventory import Device


class RestCallService(Service):

    __tablename__ = "RestCallService"

    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    call_type = Column(SmallString)
    rest_url = Column(LargeString, default="")
    payload = Column(JSON, default={})
    params = Column(JSON, default={})
    headers = Column(JSON, default={})
    verify_ssl_certificate = Column(Boolean, default=True)
    timeout = Column(Integer, default=15)
    conversion_method = Column(SmallString, default="none")
    validation_method = Column(SmallString)
    content_match = Column(LargeString, default="")
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict)
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)
    username = Column(SmallString)
    password = Column(SmallString)

    request_dict = {
        "GET": rest_get,
        "POST": rest_post,
        "PUT": rest_put,
        "DELETE": rest_delete,
        "PATCH": rest_patch,
    }

    __mapper_args__ = {"polymorphic_identity": "RestCallService"}

    def job(self, run: "Run", payload: dict, device: Optional[Device] = None) -> dict:
        rest_url = run.sub(run.rest_url, locals())
        run.log("info", f"Sending REST call to {rest_url}")
        kwargs = {
            p: run.sub(getattr(self, p), locals())
            for p in ("headers", "params", "timeout")
        }
        if run.call_type in ("GET", "DELETE"):
            response = self.request_dict[run.call_type](
                rest_url,
                auth=HTTPBasicAuth(self.username, self.password),
                verify=run.verify_ssl_certificate,
                **kwargs,
            )
        else:
            response = self.request_dict[run.call_type](
                rest_url,
                data=dumps(run.sub(run.payload, locals())),
                auth=HTTPBasicAuth(self.username, self.password),
                verify=run.verify_ssl_certificate,
                **kwargs,
            )
        if response.status_code not in range(200, 300):
            result = {
                "success": False,
                "response_code": response.status_code,
                "response": response.text,
            }
            if response.status_code == 401:
                result["error"] = "Wrong credentials supplied."
            return result
        result = run.convert_result(response.text)
        match = (
            run.sub(run.content_match, locals())
            if run.validation_method == "text"
            else run.sub(run.dict_match, locals())
        )
        return {
            "url": rest_url,
            "match": match,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "negative_logic": run.negative_logic,
            "result": result,
            "success": run.match_content(result, match),
        }


class RestCallForm(ServiceForm, ValidationForm):
    form_type = HiddenField(default="RestCallService")
    has_targets = BooleanField("Has Target Devices", default=True)
    call_type = SelectField(
        choices=(
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("DELETE", "DELETE"),
            ("PATCH", "PATCH"),
        )
    )
    rest_url = SubstitutionField()
    payload = JsonSubstitutionField()
    params = DictSubstitutionField()
    headers = DictSubstitutionField()
    verify_ssl_certificate = BooleanField("Verify SSL Certificate")
    timeout = IntegerField(default=15)
    username = StringField()
    password = PasswordField()
    groups = {
        "Main Parameters": {
            "commands": [
                "has_targets",
                "call_type",
                "rest_url",
                "payload",
                "params",
                "headers",
                "verify_ssl_certificate",
                "timeout",
                "username",
                "password",
            ],
            "default": "expanded",
        },
        "Validation Parameters": ValidationForm.group,
    }
