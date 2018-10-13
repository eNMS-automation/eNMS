from sqlalchemy import Boolean, Column, ForeignKey, Integer

from eNMS.automation.models import Service, service_classes


class SwissArmyKnifeService(Service):

    __tablename__ = 'SwissArmyKnifeService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = Column(Boolean)

    __mapper_args__ = {
        'polymorphic_identity': 'swiss_army_knife_service',
    }

    def job(self, *args):
        return getattr(self, self.name)(*args)

    # Instance call "job1" with has_targets set to True
    def job1(self, device, payload):
        return {'success': True, 'result': ''}

    # Instance call "job2" with has_targets set to False
    def job2(self, payload):
        return {'success': True, 'result': ''}

    def process_payload1(self, payload):
        get_int = payload['get_interfaces']
        r8_int = get_int['devices']['router8']['result']['get_interfaces']
        speed_fa0 = r8_int['FastEthernet0/0']['speed']
        speed_fa1 = r8_int['FastEthernet0/1']['speed']
        same_speed = speed_fa0 == speed_fa1

        get_facts = payload['get_facts']
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
