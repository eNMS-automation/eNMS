from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.services.models import Service, service_classes


class ProcessPayloadService(Service):

    __tablename__ = 'ProcessPayloadService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    process_function = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'process_payload_service',
    }

    def job(self, task, incoming_payload):
        process = getattr(self, self.process_function)(incoming_payload)
        results = {'success': process, 'result': process}
        return results

    def process_payload1(self, payload):
        config = payload['task_service_napalm_getter_get_config']['success']
        intf = payload['task_service_napalm_getter_get_interfaces']['success']
        return config and intf


service_classes['Process Payload Service'] = ProcessPayloadService
