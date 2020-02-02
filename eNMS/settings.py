from pathlib import Path
from json import load

with open(Path.cwd() / "settings.json", "r") as file:
    settings = load(file)
