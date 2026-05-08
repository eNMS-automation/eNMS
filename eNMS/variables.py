from base64 import urlsafe_b64encode
from collections import defaultdict
from datetime import datetime
from functools import wraps
from git import Repo
from json import load
from logging import error
from netmiko.ssh_dispatcher import CLASS_MAPPER
from os import getenv, urandom
from pathlib import Path
from random import randint
from string import punctuation
from sys import modules
from textwrap import indent
from time import time
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

try:
    from ncclient.devices import supported_devices_cfg
except ImportError as exc:
    warn(f"Couldn't import ncclient module ({exc})")

try:
    from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
except ImportError as exc:
    warn(f"Couldn't import napalm module ({exc})")


class VariableStore:
    def __init__(self):
        self._set_setup_variables()
        self._set_server_variables()
        self._set_automation_variables()
        self._set_general_variables()
        self._set_custom_variables()
        self._set_configuration_variables()
        self._set_report_variables()
        self._set_run_variables()
        self._set_version()
        self._set_plugins_settings()
        self._set_timing_mixin()
        self._update_rbac_variables()

    def _set_automation_variables(self):
        self.ssh_sessions = {}
        self.netmiko_drivers = sorted(CLASS_MAPPER)
        self.scrapli_drivers = sorted(CORE_PLATFORM_MAP)
        self.timestamps = (
            "status",
            "update",
            "failure",
            "runtime",
            "duration",
            "success",
        )
        self.configuration_properties = {
            "configuration": "Configuration",
            "operational_data": "Operational Data",
            "specialized_data": "Specialized Data",
        }
        try:
            self.napalm_drivers = sorted(SUPPORTED_DRIVERS[1:])
        except NameError:
            self.napalm_drivers = []
        try:
            self.netconf_drivers = sorted(supported_devices_cfg)
        except NameError:
            self.netconf_drivers = []

    def _set_configuration_variables(self):
        for property, title in self.configuration_properties.items():
            self.properties["filtering"]["device"].append(property)
            self.properties["tables"]["configuration"].insert(
                -3,
                {
                    "data": property,
                    "title": title,
                    "search": "text",
                    "width": "70%",
                    "visible": property == "configuration",
                    "orderable": False,
                    "html": True,
                },
            )
            for timestamp in self.timestamps:
                self.properties["tables"]["configuration"].insert(
                    -3,
                    {
                        "data": f"last_{property}_{timestamp}",
                        "title": f"Last {title} {timestamp.capitalize()}",
                        "search": "text",
                        "visible": False,
                        "html": timestamp == "status",
                    },
                )

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

    def _set_report_variables(self):
        self.reports = {"Empty report": ""}
        for path in Path(self.file_path / "reports").glob("**/*"):
            if path.suffix not in {".j2", ".txt"}:
                continue
            with open(path, "r") as file:
                self.reports[path.name] = file.read()

    def _set_run_variables(self):
        self.run_allowed_targets = {}
        self.run_services = defaultdict(set)
        self.run_states = defaultdict(dict)
        self.run_logs = defaultdict(lambda: defaultdict(list))
        self.run_stop = defaultdict(bool)
        self.run_instances = {}
        libraries = ("netmiko", "napalm", "scrapli", "ncclient")
        self.connections_cache = {library: defaultdict(dict) for library in libraries}
        self.service_run_count = defaultdict(int)
        self.service_report = defaultdict(dict)
        self.service_result = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        self.service_changelog = defaultdict(list)

    def _set_server_variables(self):
        self.server = getenv("SERVER_NAME", "Localhost")
        self.server_ip = getenv("SERVER_ADDR", "0.0.0.0")
        self.server_role = getenv("SERVER_ROLE", "primary")
        self.scheduler_address = getenv("SCHEDULER_ADDR", "0.0.0.0")
        self.scheduler_active = getenv("SCHEDULER_ACTIVE", "1") == "1"
        self.server_url = getenv("SERVER_URL", "https://0.0.0.0")
        self.ssh_url = getenv("SSH_URL")
        self.server_location = getenv("SERVER_LOCATION")
        self.server_version = self.settings["app"]["version"]
        self.server_commit_sha = Repo(search_parent_directories=True).head.object.hexsha
        self.server_dict = {
            "name": self.server,
            "url": self.server_url,
            "ip_address": self.server_ip,
            "role": self.server_role,
        }

    def _set_setup_variables(self):
        self.path = Path.cwd()
        for setup_file in Path(getenv("SETUP_DIR", self.path / "setup")).glob("*.json"):
            with open(setup_file, "r") as file:
                setattr(self, setup_file.stem, load(file))
        self.file_path = Path(
            self.settings["paths"]["files"] or str(self.path / "files")
        )
        self.playbook_path = (
            self.settings["paths"]["playbooks"] or f"{self.file_path}/playbooks"
        )
        self.migration_path = (
            self.settings["paths"]["migration"] or f"{self.file_path}/migrations"
        )

    def _set_timing_mixin(self):
        self.profiling = {}

        class TimingMixin:
            def __getattribute__(self, name):
                attr = super().__getattribute__(name)
                if callable(attr):

                    def timed_function(*args, **kwargs):
                        start_time = time()
                        result = attr(*args, **kwargs)
                        path = f"{type(self).__name__}_{name}"
                        elapsed_time = time() - start_time
                        if path not in vs.profiling:
                            vs.profiling[path] = {
                                "count": 0,
                                "average_time": 0,
                                "combined_time": 0,
                                "class": type(self).__name__,
                            }
                        data = vs.profiling[path]
                        data["average_time"] = (
                            data["average_time"] * data["count"] + elapsed_time
                        ) / (data["count"] + 1)
                        data["count"] += 1
                        data["combined_time"] += elapsed_time
                        return result

                    return timed_function
                return attr

        self.TimingMixin = TimingMixin if self.settings["app"]["profiling"] else object

    def _set_version(self):
        with open(self.path / "package.json") as package_file:
            self.version = load(package_file)["version"]

    def _update_rbac_variables(self):
        self.rbac = {"pages": [], "menus": [], "all_pages": {}, **self.rbac}
        for category, category_values in self.rbac["menu"].items():
            if category_values["rbac"] == "access":
                self.rbac["menus"].append(category)
            for page, page_values in category_values["pages"].items():
                self.rbac["all_pages"][f"{category} - {page}"] = page_values["endpoint"]
                if page_values["rbac"] == "access":
                    self.rbac["pages"].append(page)
                for subpage, subpage_values in page_values.get("subpages", {}).items():
                    self.rbac["all_pages"][subpage] = subpage_values["endpoint"]
                    if subpage_values["rbac"] == "access":
                        self.rbac["pages"].append(subpage)

    def custom_function(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if hasattr(self.custom, func.__name__):
                return getattr(self.custom, func.__name__)(*args, **kwargs)
            return func(*args, **kwargs)

        return wrapper

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
            return f"\n{indent(str(input), tab)}" if "\n" in str(input) else str(input)

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

    def get_persistent_id(self):
        return urlsafe_b64encode(urandom(8)).decode("utf-8").rstrip("=")

    def get_time(self, randomize=False, path=False):
        current_time = str(datetime.now())
        if randomize:
            current_time += f"{randint(1, 99999):05}"
        if path:
            current_time = current_time.translate(str.maketrans(":.", "--"))
        return current_time

    def prepend_filepath(self, value):
        return f"{self.file_path}{value}"

    def set_subtypes(self):
        self.subtypes = {
            model: {
                model_name: model_class.pretty_name
                for model_name, model_class in sorted(self.models.items())
                if issubclass(model_class, self.models[model])
                and hasattr(model_class, "pretty_name")
            }
            for model in ("link", "data", "device", "service")
        }

    def set_template_context(self):
        static_path = Path(self.path) / "eNMS" / "static" / "js" / "datastore"
        self.template_context = {
            "application_path": str(self.path),
            "datastore_files": [file.name for file in static_path.glob("*.js")],
            "file_path": str(self.file_path),
            "automation": self.automation,
            "configuration_properties": self.configuration_properties,
            "form_properties": self.form_properties,
            "names": self.property_names,
            "rbac": self.rbac,
            "relationships": self.relationships,
            "subtypes": self.subtypes,
            "server_url": self.server_url,
            "settings": self.settings,
            "ssh_url": self.ssh_url,
            "themes": self.themes,
            "table_properties": self.properties["tables"],
            "version": self.version,
            "visualization": self.visualization,
            **self.custom.server_template_context(),
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

    def space_deleter(self, input):
        return "".join(input.split())

    def str_to_date(self, value):
        milliseconds = ".%f" if "." in value else ""
        return datetime.strptime(value, f"%Y-%m-%d %H:%M:%S{milliseconds}")

    def strip_all(self, input):
        return input.translate(str.maketrans("", "", f"{punctuation} "))


vs = VariableStore()
