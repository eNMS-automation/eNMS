from collections import defaultdict
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from json import load
from logging import error
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko.ssh_dispatcher import CLASS_MAPPER
from os import getenv
from pathlib import Path
from smtplib import SMTP
from string import punctuation
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
        self.path = Path.cwd()
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
        for setup_file in (self.path / "setup").iterdir():
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
        with open(self.path / "package.json") as package_file:
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

    def dict_to_string(self, input, depth=0):
        tab = "\t" * depth
        if isinstance(input, list):
            result = "\n"
            for element in input:
                result += f"{tab}- {self.str_dict(element, depth + 1)}\n"
            return result
        elif isinstance(input, dict):
            result = ""
            for key, value in input.items():
                result += f"\n{tab}{key}: {self.str_dict(value, depth + 1)}"
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

    def send_email(
        self,
        subject,
        content,
        recipients="",
        reply_to=None,
        sender=None,
        filename=None,
        file_content=None,
    ):
        sender = sender or self.settings["mail"]["sender"]
        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = recipients
        message["Date"] = formatdate(localtime=True)
        message["Subject"] = subject
        message.add_header("reply-to", reply_to or self.settings["mail"]["reply_to"])
        message.attach(MIMEText(content))
        if filename:
            attached_file = MIMEApplication(file_content, Name=filename)
            attached_file["Content-Disposition"] = f'attachment; filename="{filename}"'
            message.attach(attached_file)
        server = SMTP(self.settings["mail"]["server"], self.settings["mail"]["port"])
        if self.settings["mail"]["use_tls"]:
            server.starttls()
            password = getenv("MAIL_PASSWORD", "")
            server.login(self.settings["mail"]["username"], password)
        server.sendmail(sender, recipients.split(","), message.as_string())
        server.close()

    def strip_all(self, input):
        return input.translate(str.maketrans("", "", f"{punctuation} "))


vs = VariableStore()
