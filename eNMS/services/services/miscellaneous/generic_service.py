from sqlalchemy import Column, ForeignKey, Integer

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
        int_r8 = payload['task_service_napalm_getter_get_interfaces']['router8']
        result_int_r8 = int_r8['result']['get_interfaces']
        speed_Fa0 = result_int_r8['FastEthernet0/0']['speed']
        speed_Fa1 = result_int_r8['FastEthernet0/1']['speed']
        same_speed = speed_Fa0 == speed_Fa1
        
        facts_r8 = payload['task_service_napalm_getter_get_facts']['success']
        result_facts_r8 = facts_r8['result']['get_facts']
        uptime_less_than_50000 = result_facts_r8['uptime'] < 50000
        return {
            'success': success,
            'result': {
                'same_speed_Fa0_Fa1': same_speed,
                'uptime_less_5000': uptime_less_than_50000
            }
        }


service_classes['Generic Service'] = GenericService
