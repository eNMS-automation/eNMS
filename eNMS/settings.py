from pathlib import Path
from json import load

with open(Path.cwd() / "settings" / "app.json", "r") as file:
    settings = load(file)

with open(Path.cwd() / "settings" / "tables.json", "r") as file:
    table_properties = load(file)

with open(Path.cwd() / "settings" / "dashboard.json", "r") as file:
    dashboard_properties = load(file)

with open(Path.cwd() / "settings" / "pools.json", "r") as file:
    pool_properties = load(file)
