from subprocess import check_output
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class UnixCommandService(Service):

    __tablename__ = 'UnixCommandService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    command = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'UnixCommandService',
    }

    def job(self, *args):
        if len(args) == 2:
            device, payload = args
        try:
            command = self.sub(self.command, locals()
            return check_output(command).split()).decode()
        except Exception as e:
            return {'success': False, 'result': str(e)}


service_classes['UnixCommandService'] = UnixCommandService
