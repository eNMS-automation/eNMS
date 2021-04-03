from json import load
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko.ssh_dispatcher import CLASS_MAPPER
from pathlib import Path
from warnings import warn

try:
    from scrapli import Scrapli

    CORE_PLATFORM_MAP = {driver: driver for driver in Scrapli.CORE_PLATFORM_MAP}
except ImportError as exc:
    CORE_PLATFORM_MAP = {"cisco_iosxe": "cisco_iosxe"}
    warn(f"Couldn't import scrapli module ({exc})")


class VariableStore(dict):
    def __init__(self):
        self.load_setup_variables()
        self.load_automation_drivers()

    def __setattr__(self, key, value):
        self[key] = value

    def load_setup_variables(self):
        for setup_file in (Path.cwd() / "setup").iterdir():
            with open(setup_file, "r") as file:
                setattr(self, setup_file.stem, load(file))

    def load_automation_drivers(self):
        self.netmiko_drivers = sorted((driver, driver) for driver in CLASS_MAPPER)
        self.napalm_drivers = sorted(
            (driver, driver) for driver in SUPPORTED_DRIVERS[1:]
        )
        self.scrapli_drivers = CORE_PLATFORM_MAP


locals().update(VariableStore())
