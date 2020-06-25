from pathlib import Path
from json import load

for setup_file in (Path.cwd() / "setup").iterdir():
    with open(setup_file, "r") as file:
        locals()[setup_file.stem] = load(file)


def update_setup_file(old, new):
    def rec(old, new):
        for k, v in new.items():
            if k not in old:
                old[k] = v
            else:
                old_value = old[k]
                if isinstance(old_value, list):
                    old_value.extend(v)
                elif isinstance(old_value, dict):
                    rec(old_value, v)
                else:
                    old[k] = v

    rec(old, new)
    return old
