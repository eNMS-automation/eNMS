from logging import info
from json import dumps, loads
from json.decoder import JSONDecodeError
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from subprocess import check_output

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class AnsiblePlaybookService(Service):

    __tablename__ = 'AnsiblePlaybookService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = Column(Boolean)
    playbook_path = Column(String)
    arguments = Column(String)
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
    options = Column(MutableDict.as_mutable(PickleType), default={})
    pass_device_properties = Column(Boolean)

    __mapper_args__ = {
        'polymorphic_identity': 'AnsiblePlaybookService',
    }

    def job(self, device, _):
        arguments = self.sub(self.arguments, locals()).split()
        command, extra_args = ['ansible-playbook'], {}
        if self.pass_device_properties:
            extra_args = device.get_properties()
            extra_args['password'] = device.password
        if self.options:
            extra_args.update(self.options)
        if extra_args:
            command.extend(['-e', dumps(extra_args)])
        if self.has_targets:
            command.extend(['-i', device.ip_address + ','])
        command.append(self.sub(self.playbook_path, locals()))
        info(f"Sending Ansible playbook: {' '.join(command + arguments)}")
        result = check_output(command + arguments)
        info(result)
        try:
            result = result.decode('utf-8')
        except AttributeError:
            pass
        try:
            result = loads(result)
        except JSONDecodeError:
            pass
        if self.validation_method == 'text':
            success = self.match_content(
                str(result),
                self.sub(self.content_match, locals())
            )
        else:
            success = self.match_dictionnary(result)
        return {
            'negative_logic': self.negative_logic,
            'result': result,
            'success': success
        }


service_classes['AnsiblePlaybookService'] = AnsiblePlaybookService
