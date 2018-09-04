from nornir.core import Nornir
from nornir.core.inventory import Inventory
from nornir.plugins.tasks import networking

parameters = {
    'name': 'nornir ping 23 443',
    'node_multiprocessing': True,
    'description': 'Uses Nornir to ping',
    'vendor': 'none',
    'operating_system': 'all'
}


def job(args):
    # Script that uses Nornir to ping a device
    task, node, results = args
    nornir_inventory = {node.name: {'nornir_ip': node.ip_address}}
    external = Nornir(inventory=Inventory(nornir_inventory), dry_run=True)
    ping_result = external.run(networking.tcp_ping, ports=[23, 443])
    return {
        'success': all(res for res in ping_result[node.name].result.keys()),
        'logs': str(ping_result[node.name].result)
    }
