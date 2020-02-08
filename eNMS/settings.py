from pathlib import Path
from json import load

with open(Path.cwd() / "settings.json", "r") as file:
    settings = load(file)

with open(Path.cwd() / "properties.json", "r") as file:
    table_properties = load(file)