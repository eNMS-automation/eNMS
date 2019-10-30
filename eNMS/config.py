from pathlib import Path
from json import load

with open(Path.cwd() / "config.json", "r") as file:
    config = load(file)
