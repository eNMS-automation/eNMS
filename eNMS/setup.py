from pathlib import Path
from json import load

with open(Path.cwd() / "settings.json", "r") as file:
    settings = load(file)

with open(Path.cwd() / "rbac.json", "r") as file:
    rbac = load(file)

with open(Path.cwd() / "setup" / "properties.json", "r") as file:
    properties = load(file)
