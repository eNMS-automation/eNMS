from pathlib import Path
from json import load

with open(Path.cwd() / "setup" / "settings.json", "r") as file:
    settings = load(file)

with open(Path.cwd() / "setup" / "rbac.json", "r") as file:
    rbac = load(file)

with open(Path.cwd() / "setup" / "properties.json", "r") as file:
    properties = load(file)

with open(Path.cwd() / "setup" / "scheduler.json", "r") as file:
    scheduler = load(file)
