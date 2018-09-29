# This class serves as a template example for the user to understand
# how to implement their own custom services to eNMS.
# It can be removed if you are deploying eNMS in production.

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


class ExampleMultiprocessingService(Service):

    __tablename__ = 'ExampleMultiprocessingService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    # The "vendor" property will be displayed as a drop-down list, because
    # there is an associated "vendor_values" property in the class.
    vendor = Column(String)
    # The "operating_system" property will be displayed as a text area.
    operating_system = Column(String)
    # Text area
    an_integer = Column(Integer)
    # Text area
    a_float = Column(Float)
    # the "a_list" property will be displayed as a multiple selection drop-down
    # list, with the values contained in "a_list_values".
    a_list = Column(MutableList.as_mutable(PickleType))
    # Text area where a python dictionnary is expected
    a_dict = Column(MutableDict.as_mutable(PickleType))
    # "boolean1" and "boolean2" will be displayed as tick boxes in the GUI.
    boolean1 = Column(Boolean)
    boolean2 = Column(Boolean)

    # these values will be displayed in a single selection drop-down list,
    # for the property "a_list".
    vendor_values = [
        ('cisco', 'Cisco'),
        ('juniper', 'Juniper'),
        ('arista', 'Arista')
    ]

    # these values will be displayed in a multiple selection drop-down list,
    # for the property "a_list".
    a_list_values = [
        ('value1', 'Value 1'),
        ('value2', 'Value 2'),
        ('value3', 'Value 3')
    ]

    __mapper_args__ = {
        'polymorphic_identity': 'example_multiprocessing_service',
    }

    def job(self, task, incoming_payload):
        # The "job" function is called when the service is executed.
        # The parameters of the service can be accessed with self (self.vendor,
        # self.boolean1, etc)
        # The target devices can be computed via "task.compute_targets()".
        # It uses the multiprocessing module to execute the service in parallel
        # on all target devices.
        # You can look at how default services (netmiko, napalm, etc.) are
        # implemented in the /services subfolders (/netmiko, /napalm, etc).
        targets = task.compute_targets()
        results = {'success': True, 'result': 'nothing happened'}
        pool = ThreadPool(processes=len(targets))
        pool.map(self.device_job, [(device, results) for device in targets])
        pool.close()
        pool.join()
        # The results is a dictionnary that will be displayed in the logs.
        # It must contain at least a key "success" that indicates whether
        # the execution of the service was a success or a failure.
        # In a workflow, the "success" value will determine whether to move
        # forward with a "Sucess" edge or a "Failure" edge.
        return results

    def device_job(self, args):
        device, results = args
        results[device.name] = True


service_classes['Example Parallel Service'] = ExampleMultiprocessingService
