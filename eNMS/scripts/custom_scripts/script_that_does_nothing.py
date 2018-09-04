parameters = {
    'name': 'script that does nothing',
    'node_multiprocessing': True,
    'description': 'does nothing',
    'vendor': 'none',
    'operating_system': 'all'
}


def job(args):
    # Script that does nothing
    task, node, results = args
    # add your own logic here
    # results is a dictionnary that contains the logs of the script
    results[node.name] = {
        'success': True,
        'logs': 'what will be displayed in the logs'
    }
