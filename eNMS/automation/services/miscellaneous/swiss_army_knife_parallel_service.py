from multiprocessing.pool import ThreadPool
from sqlalchemy import Column, ForeignKey, Integer

from eNMS.automation.models import Service, service_classes


class GenericParallelService(Service):

    __tablename__ = 'GenericParallelService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'generic_parallel_service',
    }

    def job(self, task, incoming_payload):
        targets = task.compute_targets()
        results = {'success': True, 'devices': {}}
        pool = ThreadPool(processes=len(targets))
        pool.map(
            getattr(self, self.name),
            [(task, device, incoming_payload, results) for device in targets])
        pool.close()
        pool.join()
        return results

    def job1(self, args):
        task, device, payload, results = args
        results['devices'][device.name] = True

    def job2(self, args):
        task, device, payload, results = args
        results['devices'][device.name] = True

    def job3(self, args):
        task, device, payload, results = args
        results['devices'][device.name] = True


service_classes['Generic Parallel Service'] = GenericParallelService
