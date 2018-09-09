from nornir.core import Nornir
from nornir.core.inventory import Inventory
from nornir.plugins.tasks import networking

parameters = {
    'name': 'nornir ping 23 443',
    'device_multiprocessing': True,
    'description': 'Uses Nornir to ping',
    'vendor': 'none',
    'operating_system': 'all'
}


def job(args):
    # Script that uses Nornir to ping a device
    task, device, results, payloads = args
    nornir_inventory = {device.name: {'nornir_ip': device.ip_address}}
    external = Nornir(inventory=Inventory(nornir_inventory), dry_run=True)
    ping_result = external.run(networking.tcp_ping, ports=[23, 443])
    results[device.name] = {
        'success': all(res for res in ping_result[device.name].result.keys()),
        'payload': payloads,
        'logs': str(ping_result[device.name].result)
    }
