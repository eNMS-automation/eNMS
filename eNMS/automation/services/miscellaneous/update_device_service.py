from multiprocessing.pool import ThreadPool
from sqlalchemy import Column, ForeignKey, Integer, PickleType
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.models import Service, service_classes


class UpdateDeviceService(Service):

    __tablename__ = 'UpdateDeviceService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    update_dictionnary = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {
        'polymorphic_identity': 'update_device_service',
    }

    def job(self, task, incoming_payload):
        targets = task.compute_targets()
        results = {'success': True, 'devices': {}}
        pool = ThreadPool(processes=len(targets))
        pool.map(
            self.update_device,
            [(task, device, incoming_payload, results) for device in targets])
        pool.close()
        pool.join()
        return results

    def update_device(self, args):
        task, device, payload, results = args
        try:
            for property, value in self.update_dictionnary.items():
                setattr(device, property, value)
            result, success = f'update successfully executed', False
        except Exception as e:
            result, success = f'service failed ({e})', False
            results['success'] = False
        results['devices'][device.name] = {
            'success': success,
            'result': result
        }


service_classes['update_device_service'] = UpdateDeviceService
