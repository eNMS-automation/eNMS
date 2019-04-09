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

from eNMS.automation.models import Service
from eNMS.classes import service_classes
from eNMS.inventory.models import Device


class RestCallService(Service):

    __tablename__ = "RestCallService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean)
    call_type = Column(String(255))
    url = Column(String(255))
    payload = Column(MutableDict.as_mutable(PickleType), default={})
    params = Column(MutableDict.as_mutable(PickleType), default={})
    headers = Column(MutableDict.as_mutable(PickleType), default={})
    timeout = Column(Integer, default=15.0)
    validation_method = Column(String(255))
    validation_method_values = (
        ("text", "Validation by text match"),
        ("dict_equal", "Validation by dictionary equality"),
        ("dict_included", "Validation by dictionary inclusion"),
    )
    content_match = Column(String(255))
    content_match_textarea = True
    content_match_regex = Column(Boolean)
    dict_match = Column(MutableDict.as_mutable(PickleType), default={})
    negative_logic = Column(Boolean)
    delete_spaces_before_matching = Column(Boolean)
    username = Column(String(255))
    password = Column(String(255))
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


service_classes["RestCallService"] = RestCallService
