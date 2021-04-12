from collections import defaultdict
from json import load
from logging import error
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko.ssh_dispatcher import CLASS_MAPPER
from pathlib import Path
from traceback import format_exc
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
        self._set_version()
        self._load_plugins()

    def _initialize(self):
        self._set_template_context()

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
        self.model_properties = defaultdict(lambda: ["type"])
        self.property_names = {}
        self.property_types = {}
        self.relationships = defaultdict(dict)

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

    def _set_template_context(self):
        self.template_context = {
            "configuration_properties": self.configuration_properties,
            "form_properties": self.form_properties,
            "names": self.property_names,
            "rbac": self.rbac,
            "relationships": self.relationships,
            "service_types": {
                service: service_class.pretty_name
                for service, service_class in sorted(self.models.items())
                if hasattr(service_class, "pretty_name")
            },
            "settings": self.settings,
            "themes": self.themes,
            "table_properties": self.properties["tables"],
            "version": self.version,
            "visualization": self.visualization,
        }

    def _set_version(self):
        with open(Path.cwd() / "package.json") as package_file:
            self.version = load(package_file)["version"]

    def _load_plugins(self):
        self.plugins_settings = {}
        for path in Path(self.settings["app"]["plugin_path"]).iterdir():
            if not Path(path / "settings.json").exists():
                continue
            try:
                with open(path / "settings.json", "r") as file:
                    settings = load(file)
                if not settings["active"]:
                    continue
                self.plugins_settings[path.stem] = settings
                for setup_file in ("database", "properties", "rbac"):
                    self.dictionary_recursive_merge(
                        getattr(self, setup_file), settings.get(setup_file, {})
                    )
            except Exception:
                error(f"Could not load plugin settings '{path.stem}':\n{format_exc()}")
                continue

    def dualize(self, iterable):
        return [(element, element) for element in iterable]

    def dictionary_recursive_merge(self, old, new):
        for key, value in new.items():
            if key not in old:
                old[key] = value
            else:
                old_value = old[key]
                if isinstance(old_value, list):
                    old_value.extend(value)
                elif isinstance(old_value, dict):
                    self.dictionary_recursive_merge(old_value, value)
                else:
                    old[key] = value

        return old


vs = VariableStore()
