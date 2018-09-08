parameters = {
    'name': 'Napalm Rollback',
    'device_multiprocessing': True,
    'description': 'Napalm Rollback',
    'vendor': 'All',
    'operating_system': 'All'
}


def job(args):
    # Script that does nothing
    task, device, results = args
    # add your own logic here
    # results is a dictionnary that contains the logs of the script
    results[device.name] = {
        'success': True,
        'logs': 'what will be displayed in the logs'
    }
