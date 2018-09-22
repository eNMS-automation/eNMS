from json import dumps
from multiprocessing.pool import ThreadPool
from re import search
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from subprocess import check_output

from eNMS.services.models import Service, service_classes


class AnsiblePlaybookService(Service):

    __tablename__ = 'AnsiblePlaybookService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    playbook_path = Column(String)
    arguments = Column(String)
    content_match = Column(String)
    content_match_regex = Column(Boolean)
    options = Column(MutableDict.as_mutable(PickleType), default={})
    pass_device_properties = Column(Boolean)
    inventory_from_selection = Column(Boolean)

    __mapper_args__ = {
        'polymorphic_identity': 'ansible_playbook_service',
    }

    def job(self, task, incoming_payload):
        targets = task.compute_targets()
        results = {'success': True, 'expected': self.content_match}
        pool = ThreadPool(processes=len(targets))
        pool.map(self.device_job, [(device, results) for device in targets])
        pool.close()
        pool.join()
        return results

    def device_job(self, args):
        device, results = args
        try:
            arguments = self.arguments.split()
            command = ['ansible-playbook']
            if self.pass_device_properties:
                command.extend(['-e', dumps(device.properties)])
            if self.inventory_from_selection:
                command.extend(['-i', device.ip_address + ','])
            command.append(self.playbook_path)
            result = check_output(command + arguments)
            try:
                result = result.decode('utf-8')
            except AttributeError:
                pass
            if self.content_match_regex:
                success = bool(search(self.content_match, str(result)))
            else:
                success = self.content_match in str(result)
            if not success:
                results['success'] = False
        except Exception as e:
            result, success = f'task failed ({e})', False
            results['success'] = False
        results[device.name] = {'success': success, 'result': result}



service_classes['Ansible Playbook Service'] = AnsiblePlaybookService
