from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.services.models import Service, service_classes


class GenericMultiprocessingService(Service):

    __tablename__ = 'GenericService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'generic_service',
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
        # "results" is a dictionnary that will be displayed in the logs.
        # It must contain at least a key "success" that indicates whether
        # the execution of the service was a success or a failure.
        # In a workflow, the "success" value will determine whether to move
        # forward with a "Success" edge or a "Failure" edge.
        return results

    def device_job(self, args):
        device, results = args
        results[device.name] = True


service_classes['Example Parallel Service'] = ExampleMultiprocessingService
