from collections import defaultdict
from datetime import datetime
from json import load
from logging import error
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from ncclient.devices import supported_devices_cfg
from netmiko.ssh_dispatcher import CLASS_MAPPER
from os import getenv
from pathlib import Path
from string import punctuation
from sys import modules
from traceback import format_exc
from warnings import warn
from wtforms.validators import __all__ as all_validators
from wtforms.widgets.core import __all__ as all_widgets

try:
    from scrapli import Scrapli

    CORE_PLATFORM_MAP = {driver: driver for driver in Scrapli.CORE_PLATFORM_MAP}
except ImportError as exc:
    CORE_PLATFORM_MAP = {"cisco_iosxe": "cisco_iosxe"}
    warn(f"Couldn't import scrapli module ({exc})")


class VariableStore:
    def __init__(self):
        self._set_setup_variables()
        self._set_automation_variables()
        self._set_general_variables()
        self._set_custom_variables()
        self._set_configuration_variables()
        self._set_run_variables()
        self._set_version()
        self._set_plugins_settings()
        self._update_rbac_variables()

    def _set_setup_variables(self):
        self.path = Path.cwd()
        self.server = getenv("SERVER_NAME", "Localhost")
        self.server_ip = getenv("SERVER_ADDR", "0.0.0.0")
        self.server_url = getenv("SERVER_URL", "https://0.0.0.0")
        for setup_file in (self.path / "setup").iterdir():
            with open(setup_file, "r") as file:
                setattr(self, setup_file.stem, load(file))

    def _set_automation_variables(self):
        self.ssh_sessions = {}
        self.netmiko_drivers = sorted(self.dualize(CLASS_MAPPER))
        self.napalm_drivers = sorted(self.dualize(SUPPORTED_DRIVERS[1:]))
        self.netconf_drivers = sorted(self.dualize(supported_devices_cfg))
        self.scrapli_drivers = sorted(self.dualize(CORE_PLATFORM_MAP))
        self.timestamps = ("status", "update", "failure", "runtime", "duration")
        self.configuration_properties = {
            "configuration": "Configuration",
            "operational_data": "Operational Data",
            "specialized_data": "Specialized Data",
        }

    def _set_general_variables(self):
        self.field_class = {}
        self.form_class = {}
        self.form_properties = defaultdict(dict)
        self.log_levels = ["debug", "info", "warning", "error", "critical"]
        self.models = {}
        self.model_properties = defaultdict(lambda: {"type": "str"})
        self.private_properties = self.database["private_properties"]
        self.private_properties_set = set(sum(self.private_properties.values(), []))
        self.property_names = {}
        self.relationships = defaultdict(dict)

    def _set_custom_variables(self):
        for model, values in self.properties["custom"].items():
            for property, property_dict in values.items():
                pretty_name = property_dict["pretty_name"]
                self.property_names[property] = pretty_name
                self.model_properties[model][property] = property_dict.get(
                    "type", "str"
                )
                if property_dict.get("private"):
                    if model not in self.private_properties:
                        self.private_properties[model] = []
                    self.private_properties[model].append(property)
                if model == "device" and property_dict.get("configuration"):
                    self.configuration_properties[property] = pretty_name

    def _set_configuration_variables(self):
        for property, title in self.configuration_properties.items():
            self.properties["filtering"]["device"].append(property)
            self.properties["tables"]["configuration"].insert(
                -1,
                {
                    "data": property,
                    "title": title,
                    "search": "text",
                    "width": "70%",
                    "visible": property == "configuration",
                    "orderable": False,
                },
            )
            for timestamp in self.timestamps:
                self.properties["tables"]["configuration"].insert(
                    -1,
                    {
                        "data": f"last_{property}_{timestamp}",
                        "title": f"Last {title} {timestamp.capitalize()}",
                        "search": "text",
                        "visible": False,
                    },
                )

    def _update_rbac_variables(self):
        self.rbac = {"pages": [], "menus": [], "all_pages": {}, **self.rbac}
        for category, category_values in self.rbac["menu"].items():
            if category_values["rbac"] == "access":
                self.rbac["menus"].append(category)
            for page, page_values in category_values["pages"].items():
                self.rbac["all_pages"][page] = page_values["endpoint"]
                if page_values["rbac"] == "access":
                    self.rbac["pages"].append(page)
                for subpage, subpage_values in page_values.get("subpages", {}).items():
                    self.rbac["all_pages"][subpage] = subpage_values["endpoint"]
                    if subpage_values["rbac"] == "access":
                        self.rbac["pages"].append(subpage)

    def _set_run_variables(self):
        self.run_targets = {}
        self.run_states = defaultdict(dict)
        self.run_logs = defaultdict(lambda: defaultdict(list))
        self.run_stop = defaultdict(bool)
        self.run_instances = {}
        libraries = ("netmiko", "napalm", "scrapli", "ncclient")
        self.connections_cache = {library: defaultdict(dict) for library in libraries}
        self.service_run_count = defaultdict(int)

    def set_template_context(self):
        self.template_context = {
            "application_path": str(self.path),
            "automation": self.automation,
            "configuration_properties": self.configuration_properties,
            "form_properties": self.form_properties,
            "names": self.property_names,
            "rbac": self.rbac,
            "relationships": self.relationships,
            "subtypes": {
                model: {
                    service: service_class.pretty_name
                    for service, service_class in sorted(self.models.items())
                    if issubclass(service_class, self.models[model])
                    and hasattr(service_class, "pretty_name")
                }
                for model in ("link", "node", "service")
            },
            "server_url": self.server_url,
            "settings": self.settings,
            "themes": self.themes,
            "table_properties": self.properties["tables"],
            "version": self.version,
            "visualization": self.visualization,
        }
        self.form_context = {
            **{
                validator: getattr(modules["wtforms.validators"], validator)
                for validator in all_validators
            },
            **{
                widget: getattr(modules["wtforms.widgets.core"], widget)
                for widget in all_widgets
            },
            **self.field_class,
        }

    def _set_version(self):
        with open(self.path / "package.json") as package_file:
            self.version = load(package_file)["version"]

    def _set_plugins_settings(self):
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

    def dict_to_string(self, input, depth=0):
        tab = "\t" * depth
        if isinstance(input, list):
            result = "\n"
            for element in input:
                result += f"{tab}- {self.dict_to_string(element, depth + 1)}\n"
            return result
        elif isinstance(input, dict):
            result = ""
            for key, value in input.items():
                result += f"\n{tab}{key}: {self.dict_to_string(value, depth + 1)}"
            return result
        else:
            return str(input)

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

    def get_time(self):
        return str(datetime.now())

    def strip_all(self, input):
        return input.translate(str.maketrans("", "", f"{punctuation} "))


vs = VariableStore()
