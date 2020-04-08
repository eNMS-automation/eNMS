from pathlib import Path
from ruamel import yaml


import_classes = [
    "service",
    "task",
]


def update_property(project, property, value=None, types=None):
    if not types:
        types = import_classes
    path = (
        Path.cwd()
        / "Desktop"
        / "shared"
        / "project"
        / "eNMS"
        / "files"
        / "migrations"
        / project
    )
    for instance_type in types:
        with open(path / f"{instance_type}.yaml", "r") as migration_file:
            objects = yaml.load(migration_file)
        for obj in objects:
            obj["devices"] = []
            obj["pools"] = []
        with open(path / f"{instance_type}.yaml", "w") as migration_file:
            yaml.dump(objects, migration_file)


update_property("Backup0902_devs", "devices")
