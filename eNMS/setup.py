from pathlib import Path
from json import load

for setup_file in (Path.cwd() / "setup").iterdir():
    with open(setup_file, "r") as file:
        locals()[setup_file.stem] = load(file)
