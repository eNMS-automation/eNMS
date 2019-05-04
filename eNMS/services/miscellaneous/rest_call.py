from json import dumps, loads
from requests import (
    get as rest_get,
    post as rest_post,
    put as rest_put,
    delete as rest_delete,
)
from requests.auth import HTTPBasicAuth
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField
from wtforms.widgets import TextArea

from eNMS.forms import metaform
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField
from eNMS.models import register_class
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class RestCallService(Service, metaclass=register_class):

    __tablename__ = "RestCallService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    call_type = Column(String(255), default="")
    url = Column(String(255), default="")
    payload = Column(MutableDict.as_mutable(PickleType), default={})
    params = Column(MutableDict.as_mutable(PickleType), default={})
    headers = Column(MutableDict.as_mutable(PickleType), default={})
    timeout = Column(Integer, default=15)
    validation_method = Column(String(255), default="")
    validation_method_values = (
        ("text", "Validation by text match"),
        ("dict_equal", "Validation by dictionary equality"),
        ("dict_included", "Validation by dictionary inclusion"),
    )
    content_match = Column(String(255), default="")
    content_match_textarea = True
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict.as_mutable(PickleType), default={})
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)
    username = Column(String(255), default="")
    password = Column(String(255), default="")
    call_type_values = (
        ("GET", "GET"),
        ("POST", "POST"),
        ("PUT", "PUT"),
        ("DELETE", "DELETE"),
    )

    request_dict = {
        "GET": rest_get,
        "POST": rest_post,
        "PUT": rest_put,
        "DELETE": rest_delete,
    }

    __mapper_args__ = {"polymorphic_identity": "RestCallService"}

    def job(self, payload: dict, device: Optional[Device] = None) -> dict:
        rest_url = self.sub(self.url, locals())
        self.logs.append(f"Sending REST call to {rest_url}")
        kwargs = {p: getattr(self, p) for p in ("headers", "params", "timeout")}
        if self.call_type in ("GET", "DELETE"):
            response = self.request_dict[self.call_type](
                rest_url, auth=HTTPBasicAuth(self.username, self.password), **kwargs
            )
        else:
            response = loads(
                self.request_dict[self.call_type](
                    rest_url,
                    data=dumps(self.payload),
                    auth=HTTPBasicAuth(self.username, self.password),
                    **kwargs,
                )
            )
        if response.status_code != 200:
            return {"success": False, "response_code": response.status_code}
        result = (
            response.json() if self.call_type in ("GET", "DELETE") else response.content
        )
        match = self.sub(self.content_match, locals())
        return {
            "url": rest_url,
            "match": match if self.validation_method == "text" else self.dict_match,
            "negative_logic": self.negative_logic,
            "result": result,
            "success": self.match_content(result, match),
        }


class RestCallForm(ServiceForm, metaclass=metaform):
    form_type = HiddenField(default="RestCallService")
    has_targets = BooleanField()
    call_type = SelectField(
        choices=(("GET", "GET"), ("POST", "POST"), ("PUT", "PUT"), ("DELETE", "DELETE"))
    )
    url = StringField()
    payload = DictField()
    params = DictField()
    headers = DictField()
    timeout = IntegerField(default=15)
    username = StringField()
    password = StringField()
    validation_method = SelectField(
        choices=(
            ("text", "Validation by text match"),
            ("dict_equal", "Validation by dictionary equality"),
            ("dict_included", "Validation by dictionary inclusion"),
        )
    )
    content_match = StringField(widget=TextArea(), render_kw={"rows": 5})
    content_match_regex = BooleanField()
    dict_match = DictField()
    negative_logic = BooleanField()
    delete_spaces_before_matching = BooleanField()
    pass_device_properties = BooleanField()
    options = DictField()
