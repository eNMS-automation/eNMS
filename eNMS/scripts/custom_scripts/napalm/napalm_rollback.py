from eNMS.scripts.connections import napalm_connection
from eNMS.scripts.models import multiprocessing

parameters = {
    'name': 'Napalm Rollback',
    'device_multiprocessing': True,
    'description': 'Napalm Rollback',
    'vendor': 'All',
    'operating_system': 'All'
}


@multiprocessing
def job(script, task, device, results, payloads):
    try:
        napalm_driver = napalm_connection(device)
        napalm_driver.open()
        napalm_driver.rollback()
        napalm_driver.close()
    except Exception as e:
        result = f'Napalm rollback did not work because of {e}'
        success = False
    else:
        result = 'Rollback successful'
        success = True
    return success, result, None
