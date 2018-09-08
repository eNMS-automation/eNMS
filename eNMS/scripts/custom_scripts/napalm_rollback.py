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
        getattr(napalm_driver, self.action)()
        napalm_driver.close()
    except Exception as e:
        result = f'napalm {self.action} did not work because of {e}'
        success = False
    else:
        result = self.action + ' OK'
        success = True
    results[device.name] = {'success': success, 'logs': result}
