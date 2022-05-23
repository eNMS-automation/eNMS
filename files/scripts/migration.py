from pathlib import Path
from ruamel import yaml


PATH = Path.cwd().parent.parent.parent / "eNMS" / "files" / "migrations"


def migrate_from_4_1_to_4_2(project):
    with open(PATH / project / "service.yaml", "r") as migration_file:
        services = yaml.load(migration_file)
    for service in services:
        service["priority"] += 9
        if service["type"] == "rest_call_service":
            service["custom_username"] = service.pop("username", "")
            service["custom_password"] = service.pop("password", "")
        if service["type"] == "git_service":
            actions = []
            if "git_repository" in service:
                service["local_repository"] = service.pop("git_repository")
            for action in ("add_commit", "pull", "push"):
                if service.pop(action, False):
                    actions.append(action)
            service["actions"] = actions
    with open(PATH / project / "service.yaml", "w") as migration_file:
        yaml.dump(services, migration_file)


def migrate_from_4_2_to_4_3(project):
    with open(PATH / project / "service.yaml", "r") as migration_file:
        services = yaml.load(migration_file)
    for service in services:
        if service["type"] == "netmiko_validation_service":
            service["type"] = "netmiko_commands_service
    with open(PATH / project / "service.yaml", "w") as migration_file:
        yaml.dump(services, migration_file)
