from json import dumps
from re import search
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from subprocess import check_output

from eNMS.automation.helpers import substitute
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class AnsiblePlaybookService(Service):

    __tablename__ = 'AnsiblePlaybookService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    multiprocessing = True
    playbook_path = Column(String)
    arguments = Column(String)
    content_match = Column(String)
    content_match_regex = Column(Boolean)
    options = Column(MutableDict.as_mutable(PickleType), default={})
    pass_device_properties = Column(Boolean)
    inventory_from_selection = Column(Boolean)

    __mapper_args__ = {
        'polymorphic_identity': 'AnsiblePlaybookService',
    }

    def job(self, device, payload):
        arguments = substitute(self.arguments, locals()).split()
        command = ['ansible-playbook']
        if self.pass_device_properties:
            command.extend(['-e', dumps(device.properties)])
        if self.inventory_from_selection:
            command.extend(['-i', device.ip_address + ','])
        command.append(substitute(self.playbook_path, locals()))
        result = check_output(command + arguments)
        try:
            result = result.decode('utf-8')
        except AttributeError:
            pass
        match = substitute(self.content_match, locals())
        success = (
            self.content_match_regex and bool(search(match, result))
            or match in result and not self.content_match_regex
        )
        return {'success': False, 'result': result}


service_classes['AnsiblePlaybookService'] = AnsiblePlaybookService
