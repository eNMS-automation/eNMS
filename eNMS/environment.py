from base64 import b64decode, b64encode
from click import get_current_context
from contextlib import contextmanager
from cryptography.fernet import Fernet
from dramatiq import set_broker
from dramatiq.brokers.redis import RedisBroker
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from flask_caching import Cache
from importlib import import_module
from logging import Formatter, getLogger, Handler, info
from logging.config import dictConfig
from multiprocessing import Queue
from os import getenv
from passlib.hash import argon2
from pathlib import Path
from redis import Redis
from redis.exceptions import ConnectionError, TimeoutError
from requests import Session as RequestSession
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from smtplib import SMTP
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from sys import path as sys_path, stderr
from threading import Thread
from time import perf_counter, time
from traceback import format_exc, print_exc
from warnings import warn
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

try:
    from hvac import Client as VaultClient
except ImportError:
    warn(f"Couldn't import hvac module ({format_exc()})")


from eNMS.database import db
from eNMS.variables import vs


class Environment(vs.TimingMixin):
    def __init__(self):
        if vs.settings["automation"]["task_queue"] == "dramatiq":
            self.init_dramatiq()

    def _initialize(self):
        self.init_logs()
        self.use_vault = vs.settings["vault"]["use_vault"]
        self.file_watcher = getenv("FILE_WATCHER")
        if self.file_watcher:
            return
        self.init_authentication()
        self.init_encryption()
        if self.use_vault:
            self.init_vault_client()
        if vs.settings["paths"]["custom_code"]:
            sys_path.append(vs.settings["paths"]["custom_code"])
        self.init_redis()
        self.init_connection_pools()
        self.cache = Cache(config=vs.settings["cache"]["config"])
        Path(vs.settings["files"]["trash"]).mkdir(parents=True, exist_ok=True)
        self.ssh_port = -1

    def build_multiprocessing_logging_handler(self, logging_config):
        class MultiProcessingLoggingHandler(Handler):
            def __init__(self, handler_type, **kwargs):
                super().__init__()
                module_name, class_name = handler_type.rsplit(".", 1)
                module = __import__(module_name, fromlist=[class_name])
                self.handler = getattr(module, class_name)(**kwargs)
                formatter = Formatter(vs.logging["formatters"]["standard"]["format"])
                self.handler.setFormatter(formatter)
                self.queue, thread = Queue(-1), Thread(target=self.receive)
                thread.daemon = True
                thread.start()

            def receive(self):
                while True:
                    try:
                        record = self.queue.get()
                        self.handler.emit(record)
                    except (KeyboardInterrupt, SystemExit):
                        raise
                    except EOFError:
                        break
                    except Exception:
                        print_exc(file=stderr)

            def send(self, record):
                self.queue.put_nowait(record)

            def format_record(self, record):
                if record.args:
                    record.msg = record.msg % record.args
                    record.args = None
                if record.exc_info:
                    self.format(record)
                    record.exc_info = None
                return record

            def emit(self, record):
                try:
                    formatted_record = self.format_record(record)
                    formatted_record.session = None
                    self.send(formatted_record)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception:
                    self.handleError(record)

            def close(self):
                self.handler.close()
                super().close()

        for handler_dict in logging_config["handlers"].values():
            handler_dict["()"] = MultiProcessingLoggingHandler
            handler_dict["handler_type"] = handler_dict.pop("class", None)

    @vs.custom_function
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

    def get_workers(self):
        return {worker.name: worker.to_dict() for worker in db.fetch_all("worker")}

    def init_authentication(self):
        pass

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
        if vs.logging["use_multiprocessing_handlers"]:
            self.build_multiprocessing_logging_handler(vs.logging)
        dictConfig(vs.logging)
        for logger, log_level in vs.logging["external_loggers"].items():
            info(f"Changing {logger} log level to '{log_level}'")
            log_level = getattr(import_module("logging"), log_level.upper())
            getLogger(logger).setLevel(log_level)

    @vs.custom_function
    def init_redis(self):
        host = getenv("REDIS_ADDR")
        if not host:
            self.redis_queue = None
        else:
            self.redis_queue = Redis(host=host, **vs.settings["redis"]["config"])

    @vs.custom_function
    def init_vault_client(self):
        url = getenv("VAULT_ADDR", "http://127.0.0.1:8200")
        session = None
        if "retry" in vs.settings["vault"]:
            session = RequestSession()
            adapter = HTTPAdapter(
                max_retries=Retry(**vs.settings["vault"]["retry"]),
                pool_maxsize=vs.settings["vault"].get("pool_maxsize", 25),
            )
            for address in vs.settings["vault"].get("mount", ["http://", "https://"]):
                session.mount(address, adapter)
        self.vault_client = VaultClient(
            url=url, token=getenv("VAULT_TOKEN"), session=session
        )
        if self.vault_client.sys.is_sealed() and vs.settings["vault"]["unseal_vault"]:
            keys = [getenv(f"UNSEAL_VAULT_KEY{index}") for index in range(1, 6)]
            self.vault_client.sys.submit_unseal_keys(filter(None, keys))

    def log(
        self,
        severity,
        content,
        user=None,
        change_log=True,
        logger="root",
        instance=None,
        history=None,
        runtime=None,
        source=None,
    ):
        logger_settings = vs.logging["loggers"].get(logger, {})
        if logger:
            getattr(getLogger(logger), severity)(content)
        if change_log or logger and logger_settings.get("change_log"):
            kwargs = {
                "severity": severity,
                "content": content,
                "author": user,
                "history": history,
                "source": source,
                **(instance.get_changelog_kwargs() if instance else {}),
            }
            if runtime:
                vs.service_changelog[runtime].append({"time": vs.get_time(), **kwargs})
            else:
                db.factory("changelog", **kwargs)
        vs.custom.log_post_processing(**locals())
        return logger_settings

    def log_queue(self, runtime, service, log=None, mode="add", start_line=0):
        if self.redis_queue:
            key = f"{runtime}/{service}/logs"
            vs.run_logs[runtime][int(service)] = None
            if mode == "add":
                log = self.redis("lpush", key, log)
            else:
                bound = self.redis("llen", key) - start_line - 1
                log = [] if bound == -1 else self.redis("lrange", key, 0, bound)[::-1]
        else:
            if mode == "add":
                return vs.run_logs[runtime][int(service)].append(log)
            else:
                full_log = getattr(vs.run_logs[runtime], mode)(int(service), [])
                log = full_log[start_line:]
        return log

    def monitor_filesystem(self):
        class Handler(FileSystemEventHandler):
            def on_any_event(_, event):
                src_path = event.src_path.replace(str(vs.file_path), "")
                if not src_path or any(
                    src_path.endswith(extension)
                    for extension in vs.settings["files"]["ignored_types"]
                ):
                    return
                filetype = "folder" if event.is_directory else "file"
                file = db.fetch(filetype, path=src_path, allow_none=True, rbac=None)
                if event.event_type == "moved" and file:
                    file.update(
                        path=event.dest_path.replace(str(vs.file_path), ""),
                        move_file=False,
                    )
                elif event.event_type in ("created", "modified"):
                    file = db.factory(filetype, path=src_path, rbac=None)
                elif event.event_type != "deleted" or not file:
                    return
                file.status = event.event_type.capitalize()
                if vs.settings["files"]["log_events"]:
                    log = f"File {src_path} {event.event_type} (watchdog)."
                    self.log("info", log, change_log=True)
                try:
                    db.session.commit()
                except (StaleDataError, IntegrityError):
                    db.session.rollback()

        event_handler = Handler()
        observer = PollingObserver(timeout=vs.settings["files"]["polling_interval"])
        observer.schedule(event_handler, path=str(vs.file_path), recursive=True)
        observer.start()
        try:
            observer.join()
        except KeyboardInterrupt:
            observer.stop()

    def redis(self, operation, *args, **kwargs):
        try:
            return getattr(self.redis_queue, operation)(*args, **kwargs)
        except (ConnectionError, TimeoutError) as exc:
            self.log("error", f"Redis Queue Unreachable ({exc})", change_log=False)

    @vs.custom_function
    def send_email(
        self,
        subject,
        content,
        bcc="",
        recipients="",
        reply_to=None,
        sender=None,
        filename=None,
        file_content=None,
        content_type="plain",
    ):
        sender = sender or vs.settings["mail"]["sender"]
        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = recipients
        message["Date"] = formatdate(localtime=True)
        message["Subject"] = subject
        message.add_header("reply-to", reply_to or vs.settings["mail"]["reply_to"])
        message.attach(MIMEText(content, content_type))
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
            all_recipients = recipients.split(",") if recipients else []
            all_recipients += bcc.split(",") if bcc else []
            server.sendmail(sender, all_recipients, message.as_string())

    @contextmanager
    def timer(self, description):
        start = perf_counter()
        yield
        self.log(
            "debug", f"{description}: {perf_counter() - start:.3f}s", change_log=False
        )


env = Environment()
