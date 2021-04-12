from base64 import b64decode, b64encode
from click import get_current_context
from cryptography.fernet import Fernet
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from flask_login import current_user
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from json import load
from logging.config import dictConfig
from logging import getLogger, error, info
from os import getenv
from passlib.hash import argon2
from pathlib import Path
from redis import Redis
from redis.exceptions import ConnectionError, TimeoutError
from requests import Session as RequestSession
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from smtplib import SMTP
from string import punctuation
from sqlalchemy.exc import InvalidRequestError
from sys import path as sys_path
from traceback import format_exc
from warnings import warn

try:
    from hvac import Client as VaultClient
except ImportError as exc:
    warn(f"Couldn't import hvac module ({exc})")

from eNMS.custom import CustomApp
from eNMS.database import db
from eNMS.variables import vs


class App:
    def __init__(self):
        self.path = Path.cwd()
        self.custom = CustomApp(self)
        self.custom.pre_init()
        self.load_custom_properties()
        self.load_configuration_properties()
        self.init_rbac()
        self.init_encryption()
        self.use_vault = vs.settings["vault"]["use_vault"]
        if self.use_vault:
            self.init_vault_client()
        if vs.settings["paths"]["custom_code"]:
            sys_path.append(vs.settings["paths"]["custom_code"])
        self.init_logs()
        self.init_redis()
        self.init_scheduler()
        self.init_connection_pools()
        self.custom.post_init()

    def _initialize(self):
        self.init_services()

    def authenticate_user(self, **kwargs):
        name, password = kwargs["username"], kwargs["password"]
        if not name or not password:
            return False
        user = db.get_user(name)
        default_method = vs.settings["authentication"]["default"]
        user_method = getattr(user, "authentication", default_method)
        method = kwargs.get("authentication_method", user_method)
        if method not in vs.settings["authentication"]["methods"]:
            return False
        elif method == "database":
            if not user:
                return False
            hash = vs.settings["security"]["hash_user_passwords"]
            verify = argon2.verify if hash else str.__eq__
            user_password = self.get_password(user.password)
            success = user and user_password and verify(password, user_password)
            return user if success else False
        else:
            authentication_function = getattr(app.custom, f"{method}_authentication")
            response = authentication_function(user, name, password)
            if not response:
                return False
            elif not user:
                user = db.factory("user", authentication=method, **response)
                db.session.commit()
            return user

    def detect_cli(self):
        try:
            return get_current_context().info_name == "flask"
        except RuntimeError:
            return False

    def encrypt_password(self, password):
        if isinstance(password, str):
            password = str.encode(password)
        return self.encrypt(password)

    def get_password(self, password):
        if not password:
            return
        if self.fernet_encryption and isinstance(password, str):
            password = str.encode(password)
        return str(self.decrypt(password), "utf-8")

    def get_time(self):
        return str(datetime.now())

    def init_connection_pools(self):
        self.request_session = RequestSession()
        retry = Retry(**vs.settings["requests"]["retries"])
        for protocol in ("http", "https"):
            self.request_session.mount(
                f"{protocol}://",
                HTTPAdapter(max_retries=retry, **vs.settings["requests"]["pool"]),
            )

    def init_encryption(self):
        self.fernet_encryption = getenv("FERNET_KEY")
        if self.fernet_encryption:
            fernet = Fernet(self.fernet_encryption)
            self.encrypt, self.decrypt = fernet.encrypt, fernet.decrypt
        else:
            self.encrypt, self.decrypt = b64encode, b64decode

    def init_logs(self):
        folder = self.path / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        with open(self.path / "setup" / "logging.json", "r") as logging_config:
            logging_config = load(logging_config)
        dictConfig(logging_config)
        for logger, log_level in logging_config["external_loggers"].items():
            info(f"Changing {logger} log level to '{log_level}'")
            log_level = getattr(import_module("logging"), log_level.upper())
            getLogger(logger).setLevel(log_level)

    def init_rbac(self):
        self.rbac = {"pages": [], **vs.rbac}
        for _, category in vs.rbac["menu"].items():
            for page, page_values in category["pages"].items():
                if page_values["rbac"] == "access":
                    self.rbac["pages"].append(page)
                for subpage, subpage_values in page_values.get("subpages", {}).items():
                    if subpage_values["rbac"] == "access":
                        self.rbac["pages"].append(subpage)

    def init_redis(self):
        host = getenv("REDIS_ADDR")
        self.redis_queue = (
            Redis(
                host=host,
                port=6379,
                db=0,
                charset="utf-8",
                decode_responses=True,
                socket_timeout=0.1,
            )
            if host
            else None
        )

    def init_scheduler(self):
        self.scheduler_address = getenv("SCHEDULER_ADDR")

    def init_services(self):
        path_services = [self.path / "eNMS" / "services"]
        load_examples = vs.settings["app"].get("startup_migration") == "examples"
        if vs.settings["paths"]["custom_services"]:
            path_services.append(Path(vs.settings["paths"]["custom_services"]))
        for path in path_services:
            for file in path.glob("**/*.py"):
                if "init" in str(file):
                    continue
                if not load_examples and "examples" in str(file):
                    continue
                info(f"Loading service: {file}")
                spec = spec_from_file_location(file.stem, str(file))
                try:
                    spec.loader.exec_module(module_from_spec(spec))
                except InvalidRequestError as exc:
                    error(f"Error loading custom service '{file}' ({str(exc)})")

    def init_vault_client(self):
        url = getenv("VAULT_ADDR", "http://127.0.0.1:8200")
        self.vault_client = VaultClient(url=url, token=getenv("VAULT_TOKEN"))
        if self.vault_client.sys.is_sealed() and vs.settings["vault"]["unseal_vault"]:
            keys = [getenv(f"UNSEAL_VAULT_KEY{i}") for i in range(1, 6)]
            self.vault_client.sys.submit_unseal_keys(filter(None, keys))

    def load_custom_properties(self):
        for model, values in vs.properties["custom"].items():
            for property, property_dict in values.items():
                pretty_name = property_dict["pretty_name"]
                vs.property_names[property] = pretty_name
                vs.model_properties[model].append(property)
                if property_dict.get("private"):
                    if model not in db.private_properties:
                        db.private_properties[model] = []
                    db.private_properties[model].append(property)
                if model == "device" and property_dict.get("configuration"):
                    vs.configuration_properties[property] = pretty_name

    def load_configuration_properties(self):
        for property, title in vs.configuration_properties.items():
            vs.properties["filtering"]["device"].append(property)
            vs.properties["tables"]["configuration"].insert(
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
            for timestamp in vs.configuration_timestamps:
                vs.properties["tables"]["configuration"].insert(
                    -1,
                    {
                        "data": f"last_{property}_{timestamp}",
                        "title": f"Last {title} {timestamp.capitalize()}",
                        "search": "text",
                        "visible": False,
                    },
                )

    def log(self, severity, content, user=None, change_log=True, logger="root"):
        logger_settings = vs.logging["loggers"].get(logger, {})
        if logger:
            getattr(getLogger(logger), severity)(content)
        if change_log or logger and logger_settings.get("change_log"):
            db.factory(
                "changelog",
                **{
                    "severity": severity,
                    "content": content,
                    "user": user or getattr(current_user, "name", ""),
                },
            )
        return logger_settings

    def log_queue(self, runtime, service, log=None, mode="add", start_line=0):
        if self.redis_queue:
            key = f"{runtime}/{service}/logs"
            vs.run_logs[runtime][int(service)] = None
            if mode == "add":
                log = self.redis("lpush", key, log)
            else:
                log = self.redis("lrange", key, 0, -1)
                if log:
                    log = log[::-1][start_line:]
        else:
            if mode == "add":
                return vs.run_logs[runtime][int(service)].append(log)
            else:
                full_log = getattr(vs.run_logs[runtime], mode)(int(service), [])
                log = full_log[start_line:]
        return log

    def redis(self, operation, *args, **kwargs):
        try:
            return getattr(self.redis_queue, operation)(*args, **kwargs)
        except (ConnectionError, TimeoutError) as exc:
            self.log("error", f"Redis Queue Unreachable ({exc})", change_log=False)

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
        sender = sender or vs.settings["mail"]["sender"]
        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = recipients
        message["Date"] = formatdate(localtime=True)
        message["Subject"] = subject
        message.add_header("reply-to", reply_to or vs.settings["mail"]["reply_to"])
        message.attach(MIMEText(content))
        if filename:
            attached_file = MIMEApplication(file_content, Name=filename)
            attached_file["Content-Disposition"] = f'attachment; filename="{filename}"'
            message.attach(attached_file)
        server = SMTP(vs.settings["mail"]["server"], vs.settings["mail"]["port"])
        if vs.settings["mail"]["use_tls"]:
            server.starttls()
            password = getenv("MAIL_PASSWORD", "")
            server.login(vs.settings["mail"]["username"], password)
        server.sendmail(sender, recipients.split(","), message.as_string())
        server.close()

    def str_dict(self, input, depth=0):
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

    def strip_all(self, input):
        return input.translate(str.maketrans("", "", f"{punctuation} "))


app = App()
