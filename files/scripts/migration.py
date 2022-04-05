from pathlib import Path
from ruamel import yaml


import_classes = ["service"]


def update_property(project, value=None, types=None):
    if not types:
        types = import_classes
    path = Path.cwd().parent.parent.parent / "eNMS" / "files" / "migrations" / project
    for instance_type in types:
        with open(path / f"{instance_type}.yaml", "r") as migration_file:
            objects = yaml.load(migration_file)
        for obj in objects:
            obj["priority"] += 9
            if obj["type"] == "rest_call_service":
                obj["custom_username"] = obj.pop("username", "")
                obj["custom_password"] = obj.pop("password", "")
            if obj["type"] == "git_service":
                actions = []
                if "git_repository" in obj:
                    obj["local_repository"] = obj.pop("git_repository")
                for action in ("add_commit", "pull", "push"):
                    if obj.get(action, False):
                        actions.append(action)
                obj["actions"] = actions
        with open(path / f"{instance_type}.yaml", "w") as migration_file:
            yaml.dump(objects, migration_file)


update_property("examples")
