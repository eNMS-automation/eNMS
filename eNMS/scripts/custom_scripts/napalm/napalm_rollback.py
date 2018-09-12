from eNMS.scripts.connections import napalm_connection

parameters = {
    'name': 'Napalm Rollback',
    'device_multiprocessing': True,
    'description': 'Configuration rollback with Napalm',
    'vendor': 'All',
    'operating_system': 'All'
}


def job(script, task, device, results, incoming_payload):
    try:
        napalm_driver = napalm_connection(device)
        napalm_driver.open()
        napalm_driver.rollback()
        napalm_driver.close()
        result, success = 'Rollback successful', True
    except Exception as e:
        result = f'Napalm rollback did not work because of {e}'
        success = False
    return success, result, incoming_payload
