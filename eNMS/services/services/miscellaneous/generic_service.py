from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.services.models import Service, service_classes


class GenericService(Service):

    __tablename__ = 'GenericService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'generic_service',
    }

    def job(self, task, incoming_payload):
        return getattr(self, self.name)(task, incoming_payload)

    def process_payload1(self, task, payload):
        config = payload['task_service_napalm_getter_get_config']['success']
        intf = payload['task_service_napalm_getter_get_interfaces']['success']
        result = config and intf
        return {'success': result, 'result': result}


service_classes['Generic Service'] = GenericService
