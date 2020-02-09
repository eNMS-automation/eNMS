from pathlib import Path
from json import load

with open(Path.cwd() / "settings.json", "r") as file:
    settings = load(file)

with open(Path.cwd() / "rbac.json", "r") as file:
    rbac = load(file)

with open(Path.cwd() / "properties" / "tables.json", "r") as file:
    table_properties = load(file)

with open(Path.cwd() / "properties" / "dashboard.json", "r") as file:
    dashboard_properties = load(file)

with open(Path.cwd() / "properties" / "pools.json", "r") as file:
    pool_properties = load(file)

with open(Path.cwd() / "properties" / "custom.json", "r") as file:
    custom_properties = load(file)
