from json import load
from pathlib import Path

from eNMS.controller import App

with open(Path.cwd() / "config.json", "r") as file:
    config = load(file)
    app = App(Path.cwd(), config)
    app.configure_database()
