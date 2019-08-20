from pathlib import Path

from eNMS import app as controller

app = controller.init_app(Path.cwd())
