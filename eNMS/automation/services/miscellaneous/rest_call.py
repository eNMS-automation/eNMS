from json import dumps, loads
from requests import (
    get as rest_get,
    post as rest_post,
    put as rest_put,
    delete as rest_delete
)
from requests.auth import HTTPBasicAuth
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    PickleType,
    String
)
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class RestCallService(Service):

    __tablename__ = 'RestCallService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = Column(Boolean)
    call_type = Column(String)
    url = Column(String)
    payload = Column(MutableDict.as_mutable(PickleType), default={})
    params = Column(MutableDict.as_mutable(PickleType), default={})
    headers = Column(MutableDict.as_mutable(PickleType), default={})
    timeout = Column(Float, default=15.)
    validation_method = Column(String)
    validation_method_values = (
        ('text', 'Validation by text match'),
        ('dict_equal', 'Validation by dictionnary equality'),
        ('dict_included', 'Validation by dictionnary inclusion')
    )
    content_match = Column(String)
    content_match_textarea = True
    content_match_regex = Column(Boolean)
    dict_match = Column(MutableDict.as_mutable(PickleType), default={})
    negative_logic = Column(Boolean)
    delete_spaces_before_matching = Column(Boolean)
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
        rest_url = self.sub(self.url, locals())
        kwargs = {
            p: getattr(self, p)
            for p in ('headers', 'params', 'timeout')
        }
        if self.call_type in ('GET', 'DELETE'):
            result = self.request_dict[self.call_type](
                rest_url,
                auth=HTTPBasicAuth(self.username, self.password),
                **kwargs
            ).json()
        else:
            result = loads(self.request_dict[self.call_type](
                rest_url,
                data=dumps(self.payload),
                auth=HTTPBasicAuth(self.username, self.password),
                **kwargs
            ).content)
        if self.validation_method == 'text':
            success = self.match_content(
                str(result),
                self.sub(self.content_match, locals())
            )
        else:
            success = self.match_dictionnary(result)
        return {
            'url': rest_url,
            'negative_logic': self.negative_logic,
            'result': result,
            'success': success
        }


service_classes['RestCallService'] = RestCallService
