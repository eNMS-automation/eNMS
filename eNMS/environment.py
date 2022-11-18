from base64 import b64decode, b64encode
from click import get_current_context
from collections import defaultdict
from cryptography.fernet import Fernet
from dramatiq.brokers.redis import RedisBroker
from dramatiq import set_broker
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from flask_login import current_user
from importlib import import_module
from json import load
from logging.config import dictConfig
from logging import getLogger, info
from os import getenv, getpid
from passlib.hash import argon2
from psutil import Process
from redis import Redis
from redis.exceptions import ConnectionError, TimeoutError
from requests import Session as RequestSession
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from smtplib import SMTP
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from sys import path as sys_path
from threading import Thread
from traceback import format_exc
from warnings import warn
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

try:
    from hvac import Client as VaultClient
except ImportError:
    warn(f"Couldn't import hvac module ({format_exc()})")

try:
    from ldap3 import Server
except ImportError as exc:
    warn(f"Couldn't import ldap3 module ({exc})")

try:
    from tacacs_plus.client import TACACSClient
except ImportError as exc:
    warn(f"Couldn't import tacacs_plus module ({exc})")

from eNMS.database import db
from eNMS.variables import vs


class Environment:
    def __init__(self):
        self.scheduler_address = getenv("SCHEDULER_ADDR")
        self.init_authentication()
        self.init_encryption()
        self.use_vault = vs.settings["vault"]["use_vault"]
        if self.use_vault:
            self.init_vault_client()
        if vs.settings["paths"]["custom_code"]:
            sys_path.append(vs.settings["paths"]["custom_code"])
        self.init_logs()
        self.init_redis()
        if vs.settings["automation"]["use_task_queue"]:
            self.init_dramatiq()
        self.init_connection_pools()
        self.file_path = vs.settings["paths"]["files"] or str(vs.path / "files")
        main_thread = Thread(target=self.monitor_filesystem)
        main_thread.daemon = True
        main_thread.start()
        self.ssh_port = -1

    def monitor_filesystem(self):
        class Handler(FileSystemEventHandler):
            def on_any_event(self, event):
                if any(
                    event.src_path.endswith(extension)
                    for extension in vs.settings["files"]["ignored_types"]
                ):
                    return
                filetype = "folder" if event.is_directory else "file"
                file = db.fetch(filetype, path=event.src_path, allow_none=True)
                if event.event_type == "moved" and file:
                    file.update(path=event.dest_path, move_file=False)
                elif event.event_type in ("created", "modified"):
                    file = db.factory(filetype, path=event.src_path)
                elif event.event_type == "deleted" and file:
                    db.delete_instance(file)
                else:
                    return
                file.status = event.event_type.capitalize()
                log = f"File {event.src_path} {event.event_type} (watchdog)."
                env.log("info", log, change_log=True)
                try:
                    db.session.commit()
                except (StaleDataError, IntegrityError):
                    db.session.rollback()

        event_handler = Handler()
        observer = PollingObserver()
        observer.schedule(event_handler, path=self.file_path, recursive=True)
        observer.start()

    def authenticate_user(self, **kwargs):
        name, password = kwargs["username"], kwargs["password"]
        if not name or not password:
            return False
        user = db.fetch("user", allow_none=True, name=name)
        default_method = vs.settings["authentication"]["default"]
        user_method = getattr(user, "authentication", default_method)
        method = kwargs.get("authentication_method", user_method)
        if (
            vs.settings["authentication"]["force_authentication_method"]
            and user
            and user.authentication != method
        ):
            return False
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
            authentication_function = getattr(vs.custom, f"{method}_authentication")
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

    def get_ssh_port(self):
        if self.redis_queue:
            self.ssh_port = self.redis("incr", "ssh_port", 1)
        else:
            self.ssh_port += 1
        start = vs.settings["ssh"]["start_port"]
        end = vs.settings["ssh"]["end_port"]
        return start + int(self.ssh_port) % (end - start)

    def init_authentication(self):
        ldap_address, tacacs_address = getenv("LDAP_ADDR"), getenv("TACACS_ADDR")
        try:
            if ldap_address:
                self.ldap_server = Server(getenv("LDAP_ADDR"))
            if tacacs_address:
                self.tacacs_client = TACACSClient(
                    getenv("TACACS_ADDR"), 49, getenv("TACACS_PASSWORD")
                )
        except NameError as exc:
            warn(f"Module missing ({exc})")

    def init_connection_pools(self):
        self.request_session = RequestSession()
        retry = Retry(**vs.settings["requests"]["retries"])
        for protocol in ("http", "https"):
            self.request_session.mount(
                f"{protocol}://",
                HTTPAdapter(max_retries=retry, **vs.settings["requests"]["pool"]),
            )

    def init_dramatiq(self):
        set_broker(
            RedisBroker(
                host=getenv("REDIS_ADDR"),
                **{
                    key: value
                    for key, value in vs.settings["redis"]["config"].items()
                    if key != "decode_responses"
                },
            )
        )

    def init_encryption(self):
        self.fernet_encryption = getenv("FERNET_KEY")
        if self.fernet_encryption:
            fernet = Fernet(self.fernet_encryption)
            self.encrypt, self.decrypt = fernet.encrypt, fernet.decrypt
        else:
            self.encrypt, self.decrypt = b64encode, b64decode

    def init_logs(self):
        folder = vs.path / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        with open(vs.path / "setup" / "logging.json", "r") as logging_config:
            logging_config = load(logging_config)
        dictConfig(logging_config)
        for logger, log_level in logging_config["external_loggers"].items():
            info(f"Changing {logger} log level to '{log_level}'")
            log_level = getattr(import_module("logging"), log_level.upper())
            getLogger(logger).setLevel(log_level)

    def init_redis(self):
        host = getenv("REDIS_ADDR")
        if not host:
            self.redis_queue = None
        else:
            self.redis_queue = Redis(host=host, **vs.settings["redis"]["config"])
            if vs.settings["redis"]["flush_on_restart"]:
                self.redis_queue.flushdb()

    def init_vault_client(self):
        url = getenv("VAULT_ADDR", "http://127.0.0.1:8200")
        self.vault_client = VaultClient(url=url, token=getenv("VAULT_TOKEN"))
        if self.vault_client.sys.is_sealed() and vs.settings["vault"]["unseal_vault"]:
            keys = [getenv(f"UNSEAL_VAULT_KEY{index}") for index in range(1, 6)]
            self.vault_client.sys.submit_unseal_keys(filter(None, keys))

    def get_workers(self):
        if not self.redis_queue:
            return {"error": "This endpoint requires the use of a Redis queue."}
        workers = defaultdict(lambda: {"jobs": {}, "info": {}})
        keys = env.redis("keys", "workers/*")
        if not keys:
            return {"error": "No data available in the Redis queue."}
        data = dict(zip(keys, env.redis("mget", *keys)))
        for key, value in data.items():
            if not value or value == "0":
                continue
            process_id, category, inner_key = key.split("/")[1:]
            workers[process_id][category][inner_key] = value
        return workers

    def update_worker_job(self, job, mode="incr"):
        if not self.redis_queue:
            return
        key = f"workers/{getpid()}"
        self.redis("set", f"{key}/info/memory", f"{Process().memory_percent()}%")
        self.redis(mode, f"{key}/jobs/{job}", 1)

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
        smtp_args = (vs.settings["mail"]["server"], vs.settings["mail"]["port"])
        with SMTP(*smtp_args) as server:
            if vs.settings["mail"]["use_tls"]:
                server.starttls()
                password = getenv("MAIL_PASSWORD", "")
                server.login(vs.settings["mail"]["username"], password)
            server.sendmail(sender, recipients.split(","), message.as_string())


env = Environment()
