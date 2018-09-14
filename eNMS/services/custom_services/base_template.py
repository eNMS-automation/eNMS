from sqlalchemy import Boolean, Column, exc, ForeignKey, Integer, String

from eNMS.services.custom_service import CustomService

class AService(CustomService):

    __tablename__ = 'AService'

    id = Column(Integer, ForeignKey('CustomService.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'a_service',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def job(self, *args):
        return True, 'a', 'a'
