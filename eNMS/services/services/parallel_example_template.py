# This file shows how to implement a parallel service in eNMS.
# A parallel service is a service that is executed on all target devices
# in parallel.
# It can be removed if you are deploying eNMS in production.
# If you want to see a few examples of parallel services, you can have a look
# at the /netmiko, /napalm and /miscellaneous subfolders in /eNMS/eNMS/services.

from multiprocessing.pool import ThreadPool
# Importing SQL Alchemy column types to handle all of the types of
# form additions that the user could have.
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


class ParallelService(Service):

    __tablename__ = 'ParallelService'

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
        'polymorphic_identity': 'parallel_service',
    }

    def job(self, task, incoming_payload):
        # The "job" function is called when the service is executed.
        # It uses the multiprocessing module to execute the service in parallel
        # on all target devices.
        targets = task.compute_targets()
        results = {'success': True, 'result': 'nothing happened'}
        pool = ThreadPool(processes=len(targets))
        pool.map(self.device_job, [(device, results) for device in targets])
        pool.close()
        pool.join()
        return results

    def device_job(self, args):
        device, results = args
        results[device.name] = True


service_classes['Parallel Service'] = ParallelService
