from pathlib import Path
from ruamel import yaml


import_classes = [
    "service",
]


def update_property(project, value=None, types=None):
    if not types:
        types = import_classes
    path = Path.cwd().parent.parent.parent / "eNMS" / "files" / "migrations" / project
    for instance_type in types:
        with open(path / f"{instance_type}.yaml", "r") as migration_file:
            objects = yaml.load(migration_file)
        for obj in objects:
            if obj["validation_condition"] != "none":
                if (
                    obj["validation_method"] == "text"
                    and obj["content_match"] == ""
                    or obj["validation_method"] == "dict_included"
                    and obj["dict_match"] == {}
                ):
                    obj["validation_condition"] = "none"
        with open(path / f"{instance_type}.yaml", "w") as migration_file:
            yaml.dump(objects, migration_file)


update_property("examples")
