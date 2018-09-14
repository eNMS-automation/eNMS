from sqlalchemy import Boolean, Column, exc, ForeignKey, Integer, String

from eNMS.scripts.custom_script import CustomScript

class AScript(CustomScript):

    __tablename__ = 'AScript'

    id = Column(Integer, ForeignKey('CustomScript.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'a_script',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def job(self, *args):
        return True, 'a', 'a'
