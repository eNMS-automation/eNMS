parameters = {
    'name': 'Base script (does nothing)',
    'device_multiprocessing': False,
    'description': 'Template example',
    'vendor': 'All',
    'operating_system': 'All'
}


def job(script, task, results, incoming_payload):
    # add your own logic here
    # results is a dictionnary that contains the logs of the script
    # target devices can be accessed via 'task.devices'
    return {'success': True, 'payload': 'Outgoing payload', 'logs': 'No result'}
