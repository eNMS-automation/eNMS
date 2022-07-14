from pathlib import Path
from ruamel import yaml


FILENAME = "scalability"
PATH = Path.cwd().parent.parent.parent / "eNMS-prod" / "files" / "migrations"
PROPERTIES = {
    "device": ("name", "rbac_read", "rbac_edit"),
    "link": ("name", "source", "destination"),
    "service": ("name", "scoped_name", "shared", "services", "type"),
}


def update_migration_files():
    for model, properties in PROPERTIES.items():
        with open(PATH / FILENAME / f"{model}.yaml", "r") as migration_file:
            instances = yaml.load(migration_file)
        updated_instances = []
        for instance in instances:
            updated_instances.append(
                {
                    property: instance[property]
                    for property in properties
                    if property in instance
                }
            )
        with open(PATH / FILENAME / f"{model}.yaml", "w") as migration_file:
            yaml.dump(updated_instances, migration_file)


update_migration_files()
