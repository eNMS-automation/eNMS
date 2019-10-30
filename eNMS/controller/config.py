from json import load
from pathlib import Path

with open(Path.cwd() / "config.json", "r") as file:
    config = load(file)
