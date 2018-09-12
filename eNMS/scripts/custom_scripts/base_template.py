parameters = {
    'name': 'Base script (does nothing)',
    'device_multiprocessing': True,
    'description': 'Template example',
    'vendor': 'All',
    'operating_system': 'All'
}


def job(script, task, results, incoming_payload):
    # add your own logic here
    # results is a dictionnary that contains the logs of the script
    return True, 'logs', 'outgoing_payload'
