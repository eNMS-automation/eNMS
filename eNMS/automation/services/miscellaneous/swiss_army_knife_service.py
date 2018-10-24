from sqlalchemy import Boolean, Column, ForeignKey, Integer

from eNMS.automation.models import Service, service_classes


class SwissArmyKnifeService(Service):

    __tablename__ = 'SwissArmyKnifeService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    multiprocessing = Column(Boolean, default=False)

    __mapper_args__ = {
        'polymorphic_identity': 'swiss_army_knife_service',
    }

    def job(self, *args):
        return getattr(self, self.name)(*args)

    # Instance call "job1" with multiprocessing set to True
    def job1(self, device, payload):
        return {'success': True, 'result': ''}

    # Instance call "job2" with multiprocessing set to False
    def job2(self, payload):
        return {'success': True, 'result': ''}

    def Start(self, *a, **kw):
        # Start of a workflow
        pass

    def End(self, *a, **kw):
        # End of a workflow
        pass

    def process_payload1(self, payload):
        get_facts = payload['get_facts']
        facts = get_facts['devices']['Washington']['result']['get_facts']
        uptime_less_than_50000 = facts['uptime'] < 50000
        return {
            'success': True,
            'result': {
                'uptime_less_5000': uptime_less_than_50000
            }
        }


service_classes['swiss_army_knife_service'] = SwissArmyKnifeService
