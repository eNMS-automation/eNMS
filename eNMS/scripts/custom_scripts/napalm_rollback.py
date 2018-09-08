parameters = {
    'name': 'Napalm Rollback',
    'device_multiprocessing': True,
    'description': 'Napalm Rollback',
    'vendor': 'All',
    'operating_system': 'All'
}


def job(args):
    task, device, results = args
    try:
        napalm_driver = napalm_connection(device)
        napalm_driver.open()
        napalm_driver.rollback()
        napalm_driver.close()
    except Exception as e:
        result = f'napalm {self.action} did not work because of {e}'
        success = False
    else:
        result = 'Rollback successful'
        success = True
    results[device.name] = {'success': success, 'logs': result}
