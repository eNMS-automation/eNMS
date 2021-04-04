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
        self._set_automation_variables()
        self._set_configuration_variables()
        self._set_general_variables()
        self._set_run_variables()
        self._set_server_variables()
        self._set_setup_variables()

    def _set_automation_variables(self):
        self.ssh_sessions = {}
        self.netmiko_drivers = sorted((driver, driver) for driver in CLASS_MAPPER)
        self.napalm_drivers = sorted(
            (driver, driver) for driver in SUPPORTED_DRIVERS[1:]
        )
        self.scrapli_drivers = CORE_PLATFORM_MAP

    def _set_configuration_variables(self):
        self.configuration_timestamps = (
            "status",
            "update",
            "failure",
            "runtime",
            "duration",
        )
        self.configuration_properties = {"configuration": "Configuration"}

    def _set_general_variables(self):
        self.form_class = {}
        self.form_properties = defaultdict(dict)
        self.models = {}
        self.property_names = {}

    def _set_run_variables(self):
        self.run_targets = {}
        self.run_states = defaultdict(dict)
        self.run_logs = defaultdict(lambda: defaultdict(list))
        self.run_stop = defaultdict(bool)
        self.run_instances = {}
        libraries = ("netmiko", "napalm", "scrapli")
        self.connections_cache = {library: defaultdict(dict) for library in libraries}
        self.service_run_count = defaultdict(int)

    def _set_server_variables(self):
        self.log_levels = ["debug", "info", "warning", "error", "critical"]
        self.status_log_level = {
            200: "info",
            401: "warning",
            403: "warning",
            404: "info",
            500: "error",
        }
        self.status_error_message = {
            401: "Wrong Credentials",
            403: "Operation not allowed.",
            404: "Invalid POST request.",
            500: "Internal Server Error.",
        }

    def _set_setup_variables(self):
        for setup_file in (Path.cwd() / "setup").iterdir():
            with open(setup_file, "r") as file:
                setattr(self, setup_file.stem, load(file))


vs = VariableStore()
