

parameters = {
    'name': 'script that does nothing',
    'device_multiprocessing': True,
    'description': 'does nothing',
    'vendor': 'none',
    'operating_system': 'all'
}


@multiprocessing
def job(task, device, results, payloads):
    # add your own logic here
    # results is a dictionnary that contains the logs of the script
    payloads['script that does nothing'] = 'script that did nothing'
    results[device.name] = {
        'success': True,
        'payload': payloads,
        'logs': 'what will be displayed in the logs'
    }
