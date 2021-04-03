from pathlib import Path
from json import load


class Variables(dict):
    def __init__(self):
        self.load_setup_variables()
        self.load_automation_variables()

    def load_setup_variables(self):
        for setup_file in (Path.cwd() / "setup").iterdir():
            with open(setup_file, "r") as file:
                self[setup_file.stem] = load(file)

    def load_automation_variables(self):
        pass

locals().update(Variables())
