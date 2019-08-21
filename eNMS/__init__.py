from pathlib import Path

from eNMS.controller import App

app = App(Path.cwd())
app.configure_database()
