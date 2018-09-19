from sqlalchemy import Column, Float, ForeignKey, Integer, String

from eNMS.services.connections import napalm_connection
from eNMS.services.models import multiprocessing, Service, service_classes


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
    device_multiprocessing = True



    __mapper_args__ = {
        'polymorphic_identity': 'ansible_playbook_service',
    }

    @multiprocessing
    def job(self, task, device, results, incoming_payload):
        try:
            napalm_driver = napalm_connection(device)
            napalm_driver.open()
            config = '\n'.join(self.content.splitlines())
            getattr(napalm_driver, self.action)(config=config)
            napalm_driver.commit_config()
            napalm_driver.close()
        except Exception as e:
            result = f'napalm config did not work because of {e}'
            success = False
        else:
            result = f'configuration OK:\n\n{config}'
            success = True
        return success, result, incoming_payload


service_classes['Ansible Playbook'] = AnsiblePlaybookService
