from eNMS.scripts.models import multiprocessing

parameters = {
    'name': 'script that does nothing',
    'device_multiprocessing': True,
    'description': 'does nothing',
    'vendor': 'All',
    'operating_system': 'All'
}


@multiprocessing
def job(script, task, device, results, incoming_payload):
    # add your own logic here
    # results is a dictionnary that contains the logs of the script
    return True, 'logs', 'Outoing payload'
