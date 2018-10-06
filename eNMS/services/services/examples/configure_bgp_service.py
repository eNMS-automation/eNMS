from multiprocessing.pool import ThreadPool
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.services.helpers import napalm_connection, NAPALM_DRIVERS
from eNMS.services.models import Service, service_classes


class NapalmConfigurationService(Service):

    __tablename__ = 'NapalmConfigurationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)


    driver = 'ios'

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_configuration_service',
    }

    def job(self, task, workflow_results):
        targets = task.compute_targets()
        results = {'success': True, 'configuration': self.content}
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
            config = '''
                ip vrf {vrf_name}
                rd {local_as}:235
                route-target import {local_as}:410
                route-target export {local_as}:400
                maximum route 10000 80

                interface Loopback {{ loopback }}
                ip vrf forwarding {vrf_name}
                ip address {loopback_ip} 255.255.255.255
                
                router bgp {local_as}
                address-family ipv4 vrf {vrf_name}
                network {{ loopback_ip }} mask 255.255.255.255
                neighbor {neighbor_ip} remote-as {remote_as}
                neighbor {neighbor_ip} activate
                neighbor {neighbor_ip} send-community both
                neighbor {neighbor_ip} as-override
                exit-address-family'''
            getattr(napalm_driver, self.action)(config=config)
            napalm_driver.commit_config()
            napalm_driver.close()
            result, success = f'Config push ({config})', True
        except Exception as e:
            result, success = f'task failed ({e})', False
            results['success'] = False
        results[device.name] = {'success': success, 'result': result}


service_classes['Napalm Configuration Service'] = NapalmConfigurationService
