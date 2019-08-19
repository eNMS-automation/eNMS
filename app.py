from pathlib import Path

from eNMS import controller


app = controller.init_app(Path.cwd())
