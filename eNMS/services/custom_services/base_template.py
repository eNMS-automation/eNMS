from sqlalchemy import Boolean, Column, exc, ForeignKey, Integer, String

from eNMS.services.custom_service import CustomService, service_classes

class AService(CustomService):

    __tablename__ = 'AService'

    id = Column(Integer, ForeignKey('CustomService.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'a_service',
    }

    form = {
        str: {
            'value1': 'value1',
            'value2': 'value2'
        },
        int: {
            'value3': 1,
            'value4': 42
        },
        dict: {
            'value5': {1: 2},
            'value6': {}
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def job(self, *args):
        return True, 'a', 'a'

service_classes['A Service'] = AService
