from json import dumps, loads
from re import search
from requests import (
    get as rest_get,
    post as rest_post,
    put as rest_put,
    delete as rest_delete
)
from requests.auth import HTTPBasicAuth
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.helpers import substitute
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class RestCallService(Service):

    __tablename__ = 'RestCallService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    multiprocessing = Column(Boolean)
    call_type = Column(String)
    url = Column(String)
    payload = Column(MutableDict.as_mutable(PickleType), default={})
    content_match = Column(String)
    content_match_regex = Column(Boolean)
    username = Column(String)
    password = Column(String)
    call_type_values = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE')
    )

    request_dict = {
        'GET': rest_get,
        'POST': rest_post,
        'PUT': rest_put,
        'DELETE': rest_delete
    }

    __mapper_args__ = {
        'polymorphic_identity': 'RestCallService',
    }

    def job(self, *args):
        if len(args) == 2:
            device, payload = args
        rest_url = substitute(self.url, locals())
        if self.call_type in ('GET', 'DELETE'):
            result = self.request_dict[self.call_type](
                rest_url,
                auth=HTTPBasicAuth(self.username, self.password)
            ).json()
        else:
            result = loads(self.request_dict[self.call_type](
                rest_url,
                data=dumps(self.payload),
                auth=HTTPBasicAuth(self.username, self.password)
            ).content)
        match = substitute(self.content_match, locals())
        success = (
            self.content_match_regex and bool(search(match, str(result)))
            or match in str(result) and not self.content_match_regex
        )
        return {'success': success, 'result': result, 'url': rest_url}


service_classes['RestCallService'] = RestCallService
