from pathlib import Path
from ruamel import yaml


import_classes = [
    "service",
]


def update_property(project, value=None, types=None):
    if not types:
        types = import_classes
    path = (
        Path.cwd()
        / "Desktop"
        / "shared"
        / "eNMS"
        / "files"
        / "migrations"
        / project
    )
    for instance_type in types:
        with open(path / f"{instance_type}.yaml", "r") as migration_file:
            objects = yaml.load(migration_file)
        for obj in objects:
            if obj["validation_method"] == "none":
                obj["validation_condition"] = "none"
                obj["validation_method"] = "text"
        with open(path / f"{instance_type}.yaml", "w") as migration_file:
            yaml.dump(objects, migration_file)


update_property("examples")
