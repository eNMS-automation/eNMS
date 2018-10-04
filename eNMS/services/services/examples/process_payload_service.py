from sqlalchemy import Column, ForeignKey, Integer

from eNMS.services.models import Service, service_classes


class ProcessPayloadService(Service):

    __tablename__ = 'ProcessPayloadService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'process_payload_service',
    }

    def job(self, task, incoming_payload):
        print(incoming_payload)
        results = {'success': True, 'result': 'nothing happened', 'test': incoming_payload}
        return results


service_classes['Process Payload Service'] = ProcessPayloadService
