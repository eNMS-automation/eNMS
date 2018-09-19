from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    PickleType,
    String
)
from sqlalchemy.ext.mutable import MutableDict, MutableList

from eNMS.services.custom_service import CustomService, service_classes

class AService(CustomService):

    __tablename__ = 'AService'

    id = Column(Integer, ForeignKey('CustomService.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    an_integer = Column(Integer)
    a_float = Column(Float)
    a_list = Column(MutableList.as_mutable(PickleType))
    a_dict = Column(MutableDict.as_mutable(PickleType))
    
    a_list_values = [
        'value1',
        'value2',
        'value3'
    ]

    __mapper_args__ = {
        'polymorphic_identity': 'a_service',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def job(self, *args):
        return True, 'a', 'a'

service_classes['A Service'] = AService
