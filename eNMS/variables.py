from collections import defaultdict
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


class VariableStore:
    def __init__(self):
        self.set_automation_variables()
        self.set_configuration_variables()
        self.set_property_variables()
        self.set_run_variables()
        self.set_setup_variables()

    def set_automation_variables(self):
        self.netmiko_drivers = sorted((driver, driver) for driver in CLASS_MAPPER)
        self.napalm_drivers = sorted(
            (driver, driver) for driver in SUPPORTED_DRIVERS[1:]
        )
        self.scrapli_drivers = CORE_PLATFORM_MAP

    def set_configuration_variables(self):
        self.configuration_timestamps = (
            "status",
            "update",
            "failure",
            "runtime",
            "duration",
        )

    def set_property_variables(self):
        self.property_names = {}

    def set_run_variables(self):
        self.run_targets = {}
        self.run_states = defaultdict(dict)
        self.run_logs = defaultdict(lambda: defaultdict(list))
        libraries = ("netmiko", "napalm", "scrapli")
        self.connections_cache = {library: defaultdict(dict) for library in libraries}
        self.service_run_count = defaultdict(int)

    def set_setup_variables(self):
        for setup_file in (Path.cwd() / "setup").iterdir():
            with open(setup_file, "r") as file:
                setattr(self, setup_file.stem, load(file))


vs = VariableStore()
