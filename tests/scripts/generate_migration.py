from pathlib import Path
from random import choice, randrange, uniform
from ruamel import yaml

service_type = [
    "swiss_army_knife_service",
    "napalm_backup_service",
    "netmiko_configuration_service",
    "netmiko_validation_service",
]


def generate_migration_file(project):
    path = Path.cwd().parent.parent.parent / "eNMS" / "files" / "migrations" / project

    services = [
        {"name": f"s{index}", "shared": True, "type": choice(service_type)}
        for index in range(1, 10001)
    ]
    with open(path / f"service.yaml", "w") as migration_file:
        yaml.dump(services, migration_file)


generate_migration_file("scalability")
