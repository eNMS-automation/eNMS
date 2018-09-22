from multiprocessing.pool import ThreadPool
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.services.helpers import napalm_connection
from eNMS.services.models import Service, service_classes


class NapalmPingService(Service):

    __tablename__ = 'NapalmPingService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    source = Column(String, default='')
    vrf = Column(String, default='')
    ttl = Column(Integer, default=255)
    timeout = Column(Integer, default=2)
    size = Column(Integer, default=100)
    count = Column(Integer, default=5)

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_ping_service',
    }

    def job(self, task, incoming_payload):
        targets = task.compute_targets()
        results = {'success': True}
        pool = ThreadPool(processes=len(targets))
        pool.map(self.device_job, [(device, results) for device in targets])
        pool.close()
        pool.join()
        return results

    def device_job(self, args):
        device, results = args
        try:
            napalm_driver = napalm_connection(device)
            napalm_driver.open()
            ping = napalm_driver.ping(
                device.ip_address,
                source=getattr(self, 'source', '')
                vrf=getattr(self, 'vrf', ''),
                ttl=getattr(self, 'ttl', '255'),
                timeout=getattr(self, 'timeout', '2'),
                size=self.size,
                count=self.count
            )
            napalm_driver.close()
            result, success = ping, True
        except Exception as e:
            result, success = f'task failed ({e})', False
            results['success'] = False
        results[device.name] = {'success': success, 'result': result}


service_classes['Napalm Ping Service'] = NapalmPingService
