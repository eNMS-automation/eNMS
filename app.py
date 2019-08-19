from pathlib import Path

from eNMS import App

app = App(Path.cwd()).create_web_app()
