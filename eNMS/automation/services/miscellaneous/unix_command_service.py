from subprocess import check_output
from sqlalchemy import Column, ForeignKey, Integer

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class UnixCommandService(Service):

    __tablename__ = 'UnixCommandService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    count = Column(Integer, default=5)

    __mapper_args__ = {
        'polymorphic_identity': 'UnixCommandService',
    }

    def job(self, device, _):
        try:
            return check_output(command.split()).decode().strip()
        except Exception as e:
            return {
                'success': False,
                'result': str(e)
            }


service_classes['UnixCommandService'] = UnixCommandService
