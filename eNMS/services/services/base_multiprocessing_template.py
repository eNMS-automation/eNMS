from multiprocessing.pool import ThreadPool
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    PickleType,
    String
)
from sqlalchemy.ext.mutable import MutableDict, MutableList

from eNMS.services.models import Service, service_classes


class AService(Service):

    __tablename__ = 'AService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    an_integer = Column(Integer)
    a_float = Column(Float)
    a_list = Column(MutableList.as_mutable(PickleType))
    a_dict = Column(MutableDict.as_mutable(PickleType))
    boolean1 = Column(Boolean)
    boolean2 = Column(Boolean)

    vendor_values = [
        ('cisco', 'Cisco'),
        ('juniper', 'Juniper'),
        ('arista', 'Arista')
    ]

    a_list_values = [
        ('value1', 'Value 1'),
        ('value2', 'Value 2'),
        ('value3', 'Value 3')
    ]

    __mapper_args__ = {
        'polymorphic_identity': 'a_service',
    }

    def job(self, task, incoming_payload):
        targets, results = self.compute_targets()
        pool = ThreadPool(processes=len(self.targets))
        pool.map(self.device_job, [(device, *args) for device in targets])
        pool.close()
        pool.join()

    def device_job(self, task, incoming_payload):
        results = {'success': True, 'result': 'nothing happened'}
        for device in task.compute_targets():
            results[device.name] = True
        return results


service_classes['A Service'] = AService
