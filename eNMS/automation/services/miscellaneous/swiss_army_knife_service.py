from sqlalchemy import Column, ForeignKey, Integer

from eNMS.automation.models import Service, service_classes


class SwissArmyKnifeService(Service):

    __tablename__ = 'SwissArmyKnifeService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'swiss_army_knife_service',
    }

    def job(self, workflow_results=None):
        return getattr(self, self.name)(task, workflow_results)

    def job1(self, workflow_results=None):
        return {'success': True, 'result': ''}

    def job2(self, workflow_results=None):
        return {'success': True, 'result': ''}

    def job3(self, workflow_results=None):
        return {'success': True, 'result': ''}

    def process_payload1(self, workflow_results=None):
        get_int = payload['task_get_interfaces']
        r8_int = get_int['devices']['router8']['result']['get_interfaces']
        speed_fa0 = r8_int['FastEthernet0/0']['speed']
        speed_fa1 = r8_int['FastEthernet0/1']['speed']
        same_speed = speed_fa0 == speed_fa1

        get_facts = payload['task_get_facts']
        r8_facts = get_facts['devices']['router8']['result']['get_facts']
        uptime_less_than_50000 = r8_facts['uptime'] < 50000
        return {
            'success': True,
            'result': {
                'same_speed_fa0_fa1': same_speed,
                'uptime_less_5000': uptime_less_than_50000
            }
        }


service_classes['swiss_army_knife_service'] = SwissArmyKnifeService
