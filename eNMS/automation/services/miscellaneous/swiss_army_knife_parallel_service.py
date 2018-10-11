from multiprocessing.pool import ThreadPool
from sqlalchemy import Column, ForeignKey, Integer

from eNMS.automation.models import Service, service_classes


class ParallelSwissArmyKnifeService(Service):

    __tablename__ = 'ParallelSwissArmyKnifeService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'sak_parallel_service',
    }

    def job(self, workflow_results=None):
        targets = self.compute_targets()
        results = {'success': True, 'devices': {}}
        pool = ThreadPool(processes=len(targets))
        pool.map(
            getattr(self, self.name),
            [(device, workflow_results, results) for device in targets])
        pool.close()
        pool.join()
        return results

    def job1(self, args):
        device, payload, results = args
        results['devices'][device.name] = True

    def job2(self, args):
        device, payload, results = args
        results['devices'][device.name] = True

    def job3(self, args):
        device, payload, results = args
        results['devices'][device.name] = True


service_classes['sak_parallel_service'] = ParallelSwissArmyKnifeService
