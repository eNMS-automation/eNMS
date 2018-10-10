from multiprocessing.pool import ThreadPool
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.automation.helpers import napalm_connection, NAPALM_DRIVERS
from eNMS.automation.models import Service, service_classes


class NapalmTracerouteService(Service):

    __tablename__ = 'NapalmTracerouteService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    driver = Column(String)
    driver_values = NAPALM_DRIVERS
    operating_system = Column(String)
    source = Column(String)
    timeout = Column(Integer)
    ttl = Column(Integer)
    vendor = Column(String)
    vrf = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_traceroute_service',
    }

    def job(self, task, workflow_results):
        targets = task.compute_targets()
        results = {'success': True, 'devices': {}}
        pool = ThreadPool(processes=len(targets))
        pool.map(self.device_job, [(device, results) for device in targets])
        pool.close()
        pool.join()
        return results

    def device_job(self, args):
        device, results = args
        try:
            napalm_driver = napalm_connection(self, device)
            napalm_driver.open()
            traceroute = napalm_driver.traceroute(
                device.ip_address,
                source=self.source,
                vrf=self.vrf,
                ttl=self.ttl or 255,
                timeout=self.timeout or 2
            )
            napalm_driver.close()
            result, success = traceroute, 'success' in traceroute
        except Exception as e:
            result, success = f'task failed ({e})', False
            results['success'] = False
        results['devices'][device.name] = {
            'success': success,
            'result': result
        }


service_classes['Napalm Traceroute Service'] = NapalmTracerouteService
