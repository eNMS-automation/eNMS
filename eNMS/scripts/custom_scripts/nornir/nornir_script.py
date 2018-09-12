from nornir.core import Nornir
from nornir.core.inventory import Inventory
from nornir.plugins.tasks import networking

from eNMS.scripts.models import multiprocessing

parameters = {
    'name': 'nornir ping 23 443',
    'device_multiprocessing': True,
    'description': 'Uses Nornir to ping',
    'vendor': 'none',
    'operating_system': 'all'
}


@multiprocessing
def job(script, task, device, results, incoming_payload):
    '''Script that uses Nornir to ping a device.'''
    nornir_inventory = {device.name: {'nornir_ip': device.ip_address}}
    external = Nornir(inventory=Inventory(nornir_inventory), dry_run=True)
    ping_result = external.run(networking.tcp_ping, ports=[23, 443])
    return (
        all(res for res in ping_result[device.name].result.keys()),
        str(ping_result[device.name].result),
        incoming_payload,
    )
