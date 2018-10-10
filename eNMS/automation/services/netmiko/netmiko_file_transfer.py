from multiprocessing.pool import ThreadPool
from netmiko import file_transfer
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from eNMS.automation.helpers import netmiko_connection, NETMIKO_SCP_DRIVERS
from eNMS.automation.models import Service, service_classes


class NetmikoFileTransferService(Service):

    __tablename__ = 'NetmikoFileTransferService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    dest_file = Column(String)
    direction = Column(String)
    direction_values = (('put', 'Upload'), ('get', 'Download'))
    disable_md5 = Column(Boolean)
    driver = Column(String)
    driver_values = NETMIKO_SCP_DRIVERS
    file_system = Column(String)
    inline_transfer = Column(Boolean)
    operating_system = Column(String)
    overwrite_file = Column(Boolean)
    source_file = Column(String)
    vendor = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_file_transfer_service',
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
            netmiko_handler = netmiko_connection(self, device)
            transfer_dict = file_transfer(
                netmiko_handler,
                source_file=self.source_file,
                dest_file=self.dest_file,
                file_system=self.file_system,
                direction=self.direction,
                overwrite_file=self.overwrite_file,
                disable_md5=self.disable_md5,
                inline_transfer=self.inline_transfer
            )
            result, success = transfer_dict, True
            netmiko_handler.disconnect()
        except Exception as e:
            result, success = f'task failed ({e})', False
            results['success'] = False
        results['devices'][device.name] = {
            'success': success,
            'result': result
        }


service_classes['netmiko_file_transfer_service'] = NetmikoFileTransferService
