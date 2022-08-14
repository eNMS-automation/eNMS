from pathlib import Path
from random import choice, randrange
from ruamel import yaml

service_type = [
    "swiss_army_knife_service",
    "napalm_backup_service",
    "netmiko_configuration_service",
    "netmiko_commands_service",
]

PATH = (
    Path.cwd().parent.parent.parent
    / "eNMS-prod"
    / "files"
    / "migrations"
    / "model_scalability"
)


def generate_services():
    services = [
        {
            "name": f"[Shared] s{index}",
            "scoped_name": f"s{index}",
            "shared": True,
            "type": choice(service_type),
        }
        for index in range(1, 30)
    ]
    services.extend(
        [
            {
                "name": f"w{index}",
                "scoped_name": f"w{index}",
                "type": "workflow",
                "services": list(
                    set(f"[Shared] s{randrange(1, 30)}" for _ in range(3))
                ),
            }
            for index in range(1, 5)
        ]
    )
    with open(PATH / "service.yaml", "w") as migration_file:
        yaml.dump(services, migration_file)


def generate_devices():
    devices = [{"name": f"d{index}"} for index in range(1, 80_001)]
    with open(PATH / "device.yaml", "w") as migration_file:
        yaml.dump(devices, migration_file)


def generate_pools():
    pools = []
    for index in range(1, 1_001):
        # we associate each pool of index (1)xyyy to a range of
        # at most 3K devices in [max(0, xK - 1), min(9, xK + 1)]
        x = index // 100
        pools.append(
            {
                "name": f"Pool {index}",
                "device_name": "d[{}-{}]\d{{3}}".format(max(x - 1, 0), min(x + 1, 9)),
                "device_name_match": "regex",
            }
        )
    for index in range(1_001, 5_001):
        pools.append(
            {
                "name": f"Pool {index}",
                "device_name": ".*",
                "device_name_match": "regex",
            }
        )
    with open(PATH / "pool.yaml", "w") as migration_file:
        yaml.dump(pools, migration_file)


def generate_users():
    users = [{"name": f"user{index}"} for index in range(1, 1_001)]
    with open(PATH / "user.yaml", "w") as migration_file:
        yaml.dump(users, migration_file)


def generate_tasks():
    users = [{"name": f"task{index}"} for index in range(1, 2_001)]
    with open(PATH / "task.yaml", "w") as migration_file:
        yaml.dump(users, migration_file)


def generate_networks():
    networks = [
        {
            "name": f"w{index}",
            "nodes": list(set(f"d{randrange(1, 80_000)}" for _ in range(30))),
        }
        for index in range(1, 1_001)
    ]
    with open(PATH / "network.yaml", "w") as migration_file:
        yaml.dump(networks, migration_file)


generate_networks()
