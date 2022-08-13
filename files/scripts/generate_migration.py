from pathlib import Path
from random import choice, randrange
from ruamel import yaml

service_type = [
    "swiss_army_knife_service",
    "napalm_backup_service",
    "netmiko_configuration_service",
    "netmiko_commands_service",
]

PATH = Path.cwd().parent.parent.parent / "eNMS-prod" / "files" / "migrations"


def generate_model_scalability_service_migration_file():
    path = PATH / "model_scalability"
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
    with open(path / "service.yaml", "w") as migration_file:
        yaml.dump(services, migration_file)


def generate_model_scalability_device_migration_file():
    path = PATH / "model_scalability"
    devices = [{"name": f"d{index}"} for index in range(1, 80_001)]
    with open(path / "device.yaml", "w") as migration_file:
        yaml.dump(devices, migration_file)


def generate_model_scalability_pool_migration_file():
    path = PATH / "model_scalability"
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
    with open(path / "pool.yaml", "w") as migration_file:
        yaml.dump(pools, migration_file)


def generate_model_scalability_user_migration_file():
    path = PATH / "model_scalability"
    users = [{"name": f"u{index}"} for index in range(1, 1_001)]
    with open(path / "user.yaml", "w") as migration_file:
        yaml.dump(users, migration_file)


generate_model_scalability_user_migration_file()
