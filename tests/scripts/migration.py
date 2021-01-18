from pathlib import Path
from ruamel import yaml


import_classes = [
    "link",
]


def update_property(project, value=None, types=None):
    if not types:
        types = import_classes
    path = Path.cwd().parent.parent.parent / "eNMS" / "files" / "migrations" / project
    for instance_type in types:
        with open(path / f"{instance_type}.yaml", "r") as migration_file:
            objects = yaml.load(migration_file)
        result = []
        for obj in objects:
            result.append(
                {
                    property: obj[property]
                    for property in ("name", "source", "destination")
                }
            )
        with open(path / f"{instance_type}.yaml", "w") as migration_file:
            yaml.dump(result, migration_file)


update_property("scalability")
