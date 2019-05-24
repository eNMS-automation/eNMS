from os import environ
from pathlib import Path

from eNMS import create_app

app = create_app(Path.cwd(), environ.get("ENMS_CONFIG_MODE", "Default"))
