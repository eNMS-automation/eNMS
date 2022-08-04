from pathlib import Path
from random import choice, randrange
from ruamel import yaml

service_type = [
    "swiss_army_knife_service",
    "napalm_backup_service",
    "netmiko_configuration_service",
    "netmiko_commands_service",
]


def generate_scalability_migration_file(project):
    path = Path.cwd().parent.parent.parent / "eNMS-prod" / "files" / "migrations" / project

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


def generate_pool_scalability_migration_file(project):
    path = Path.cwd().parent.parent.parent / "eNMS-prod" / "files" / "migrations" / project
    pools = []

    for index in range(20_000):
        # we associate each pool of index (1)xyyy
        # to a range of 3K devices in [xK - 1, xK + 1]
        x = index // 1000
        pools.append({
            "name": f"Pool n°{index}",
            "device_name": f"d[{x - 1}-{x + 1}]\d{3}",
            "device_name_match": "regex",
            "type": "pool",
        })

    with open(path / "pool.yaml", "w") as migration_file:
        yaml.dump(pools, migration_file)


generate_pool_scalability_migration_file("pool_scalability")
