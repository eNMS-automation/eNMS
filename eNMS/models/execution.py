from builtins import __dict__ as builtins
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from functools import partial
from json import dumps, loads
from json.decoder import JSONDecodeError
from multiprocessing.pool import ThreadPool
from napalm import get_network_driver
from netmiko import ConnectHandler
from os import environ
from paramiko import SFTPClient
from ruamel import yaml
from re import compile, search
from requests import post
from scp import SCPClient
from slackclient import SlackClient
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from time import sleep
from traceback import format_exc
from xmltodict import parse
from xml.parsers.expat import ExpatError

from eNMS import app
from eNMS.database import Session
from eNMS.database.associations import run_pool_table, run_device_table
from eNMS.database.dialect import Column, MutableDict, SmallString
from eNMS.database.functions import factory, fetch
from eNMS.database.base import AbstractBase
from eNMS.models import models


class Result(AbstractBase):

    __tablename__ = type = "result"
    private = True
    id = Column(Integer, primary_key=True)
    success = Column(Boolean, default=False)
    runtime = Column(SmallString)
    duration = Column(SmallString)
    result = Column(MutableDict)
    run_id = Column(Integer, ForeignKey("run.id"))
    run = relationship("Run", back_populates="results", foreign_keys="Result.run_id")
    parent_runtime = Column(SmallString)
    parent_device_id = Column(Integer, ForeignKey("device.id"))
    parent_device = relationship("Device", uselist=False, foreign_keys=parent_device_id)
    parent_device_name = association_proxy("parent_device", "name")
    device_id = Column(Integer, ForeignKey("device.id"))
    device = relationship("Device", uselist=False, foreign_keys=device_id)
    device_name = association_proxy("device", "name")
    service_id = Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", foreign_keys="Result.service_id")
    service_name = association_proxy("service", "name")
    workflow_id = Column(Integer, ForeignKey("workflow.id", ondelete="cascade"))
    workflow = relationship("Workflow", foreign_keys="Result.workflow_id")
    workflow_name = association_proxy("workflow", "name")

    def __repr__(self):
        return f"{self.service_name} on {self.device_name}"

    def __getitem__(self, key):
        return self.result[key]

    def __init__(self, **kwargs):
        self.success = kwargs["result"]["success"]
        self.runtime = kwargs["result"]["runtime"]
        self.duration = kwargs["result"]["duration"]
        super().__init__(**kwargs)
        self.parent_runtime = self.run.parent_runtime

    @property
    def table_success(self):
        btn = "success" if self.success else "danger"
        label = "Success" if self.success else "Failure"
        return (
            f'<button type="button" class="btn btn-{btn} btn-sm"'
            f'style="width:100%">{label}</button>'
        )

    def generate_row(self, **kwargs):
        return super().generate_row() + [
            f"""<button type="button" class="btn btn-info btn-sm"
            onclick="showResult('{self.id}')">Results</button>""",
            f"""<input type="radio" name="v1" value="{self.id}"/>""",
            f"""<input type="radio" name="v2" value="{self.id}"/>""",
        ]


class Run(AbstractBase):

    __tablename__ = type = "run"
    private = True
    id = Column(Integer, primary_key=True)
    restart_run_id = Column(Integer, ForeignKey("run.id"))
    restart_run = relationship("Run", uselist=False, foreign_keys=restart_run_id)
    creator = Column(SmallString, default="admin")
    properties = Column(MutableDict)
    success = Column(Boolean, default=False)
    status = Column(SmallString, default="Running")
    runtime = Column(SmallString)
    duration = Column(SmallString)
    parent_id = Column(Integer, ForeignKey("run.id"))
    parent = relationship(
        "Run", remote_side=[id], foreign_keys="Run.parent_id", back_populates="children"
    )
    children = relationship("Run", foreign_keys="Run.parent_id")
    parent_runtime = Column(SmallString)
    path = Column(SmallString)
    parent_device_id = Column(Integer, ForeignKey("device.id"))
    parent_device = relationship("Device", foreign_keys="Run.parent_device_id")
    devices = relationship("Device", secondary=run_device_table, back_populates="runs")
    pools = relationship("Pool", secondary=run_pool_table, back_populates="runs")
    service_id = Column(Integer, ForeignKey("service.id"))
    service = relationship(
        "Service", back_populates="runs", foreign_keys="Run.service_id"
    )
    service_name = association_proxy("service", "name")
    workflow_id = Column(Integer, ForeignKey("workflow.id", ondelete="cascade"))
    workflow = relationship("Workflow", foreign_keys="Run.workflow_id")
    workflow_name = association_proxy("workflow", "name")
    task_id = Column(Integer, ForeignKey("task.id"))
    task = relationship("Task", foreign_keys="Run.task_id")
    state = Column(MutableDict)
    results = relationship("Result", back_populates="run", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        self.runtime = kwargs.get("runtime") or app.get_time()
        super().__init__(**kwargs)
        if not kwargs.get("parent_runtime"):
            self.parent_runtime = self.runtime
            self.path = str(self.service.id)
        else:
            self.path = f"{self.parent.path}>{self.service.id}"

    @property
    def name(self):
        return repr(self)

    def __repr__(self):
        return f"{self.runtime} ({self.service_name} run by {self.creator})"

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        elif key in self.__dict__.get("properties", {}):
            return self.__dict__["properties"][key]
        elif self.__dict__.get("service_id"):
            return getattr(self.service, key)
        else:
            raise AttributeError

    def result(self, device=None):
        result = [r for r in self.results if r.device_name == device]
        return result.pop() if result else None

    def generate_row(self, **kwargs):
        return super().generate_row() + [
            f"""
            <ul class="pagination pagination-lg" style="margin: 0px; width: 100px">
          <li>
            <button type="button" class="btn btn-info"
            onclick="showRuntimePanel('results', {self.service.row_properties},
            '{self.runtime}')"data-tooltip="Results">
            <span class="glyphicon glyphicon-list-alt"></span></button>
          </li>
          <li>
            <button type="button" class="btn btn-info"
            onclick="showRuntimePanel('logs', {self.service.row_properties},
            '{self.runtime}')"data-tooltip="Logs">
            <span class="glyphicon glyphicon-list"></span></button>
          </li>
        </ul>"""
        ]

    @property
    def run_state(self):
        if self.state:
            return self.state
        elif self.runtime == self.parent_runtime:
            return app.run_db[self.runtime]
        else:
            return app.run_db[self.parent_runtime]["services"][self.path]

    @property
    def edge_state(self):
        return app.run_db[self.parent_runtime]["edges"]

    @property
    def stop(self):
        return self.run_state["status"] == "stop"

    @property
    def progress(self):
        if self.status == "Running":
            progress = self.run_state["progress"]["device"]
            try:
                return (
                    f"{progress['success'] + progress['failure']}/{progress['total']}"
                    f" ({progress['failure']} failed)"
                )
            except KeyError:
                return "N/A"
        else:
            return "N/A"

    def compute_devices_from_query(_self, query, property, **locals):  # noqa: N805
        values = _self.eval(query, **locals)
        devices, not_found = set(), []
        if isinstance(values, str):
            values = [values]
        for value in values:
            device = fetch("device", allow_none=True, **{property: value})
            if device:
                devices.add(device)
            else:
                not_found.append(value)
        if not_found:
            raise Exception(f"Device query invalid targets: {', '.join(not_found)}")
        return devices

    def compute_devices(self, payload):
        devices = set(self.devices)
        for pool in self.pools:
            devices |= set(pool.devices)
        if not devices:
            if self.service.device_query:
                devices |= self.compute_devices_from_query(
                    self.service.device_query,
                    self.service.device_query_property,
                    payload=payload,
                )
            devices |= set(self.service.devices)
            for pool in self.service.pools:
                devices |= set(pool.devices)
        return list(devices)

    def init_state(self):
        state = {
            "status": "Idle",
            "success": None,
            "progress": {"device": {"total": 0, "success": 0, "failure": 0}},
            "attempt": 0,
            "waiting_time": {
                "total": self.service.waiting_time,
                "left": self.service.waiting_time,
            },
            "summary": {"success": [], "failure": []},
        }
        if self.service.type == "workflow":
            state.update({"edges": defaultdict(int), "services": defaultdict(dict)})
            state["progress"]["service"] = {
                "total": len(self.service.services),
                "success": 0,
                "failure": 0,
                "skipped": 0,
            }
        if self.runtime == self.parent_runtime:
            if self.runtime in app.run_db:
                return
            app.run_db[self.runtime] = state
        else:
            service_states = app.run_db[self.parent_runtime]["services"]
            if self.path not in service_states:
                service_states[self.path] = state

    def run(self, payload):
        self.init_state()
        self.run_state["status"] = "Running"
        start = datetime.now().replace(microsecond=0)
        try:
            app.service_db[self.service.id]["runs"] += 1
            Session.commit()
            results = self.device_run(payload)
        except Exception:
            result = (
                f"Running {self.service.type} '{self.service.name}'"
                " raised the following exception:\n"
                f"{chr(10).join(format_exc().splitlines())}\n\n"
                "Run aborted..."
            )
            self.log("error", result)
            results = {"success": False, "runtime": self.runtime, "result": result}
        finally:
            Session.commit()
            results["summary"] = self.run_state.get("summary", None)
            self.status = "Aborted" if self.stop else "Completed"
            self.run_state["status"] = self.status
            if self.run_state["success"] is not False:
                self.success = self.run_state["success"] = results["success"]
            if self.send_notification:
                results = self.notify(results)
            app.service_db[self.service.id]["runs"] -= 1
            results["duration"] = self.duration = str(
                datetime.now().replace(microsecond=0) - start
            )
            results["logs"] = app.run_logs.pop(self.runtime, [])
            if self.runtime == self.parent_runtime:
                self.state = results["state"] = app.run_db.pop(self.runtime)
            if self.task and not self.task.frequency:
                self.task.is_active = False
            results["properties"] = {
                "run": self.properties,
                "service": self.service.get_properties(exclude=["positions"]),
            }
            if (
                self.runtime == self.parent_runtime
                or len(self.devices) > 1
                or self.run_method == "once"
            ):
                self.create_result(results)
            Session.commit()
        return results

    @staticmethod
    def get_device_result(args):
        device_id, runtime, payload, results = args
        device = fetch("device", id=device_id)
        run = fetch("run", runtime=runtime)
        results.append(run.get_results(payload, device))

    def device_iteration(self, payload, device):
        derived_devices = self.compute_devices_from_query(
            self.service.iteration_devices,
            self.service.iteration_devices_property,
            **locals(),
        )
        derived_run = factory(
            "run",
            **{
                "service": self.service.id,
                "devices": [derived_device.id for derived_device in derived_devices],
                "workflow": self.workflow.id,
                "parent_device": device.id,
                "restart_run": self.restart_run,
                "parent": self,
                "parent_runtime": self.parent_runtime,
            },
        )
        derived_run.properties = self.properties
        success = derived_run.run(payload)["success"]
        self.run_state["summary"]["success" if success else "failure"].append(device.name)
        return derived_run.run(payload)["success"]

    def device_run(self, payload):
        self.devices = self.compute_devices(payload)
        self.run_state["progress"]["device"]["total"] += len(self.devices)
        if self.iteration_devices and not self.parent_device:
            if not self.workflow:
                return {
                    "success": False,
                    "result": "Device iteration not allowed outside of a workflow",
                    "runtime": self.runtime,
                }
            results = [
                self.device_iteration(payload, device) for device in self.devices
            ]
            return {"success": all(results), "runtime": self.runtime}
        elif self.run_method != "per_device":
            return self.get_results(payload)
        else:
            if self.multiprocessing and len(self.devices) > 1:
                results = []
                processes = min(len(self.devices), self.max_processes)
                process_args = [
                    (device.id, self.runtime, payload, results)
                    for device in self.devices
                ]
                pool = ThreadPool(processes=processes)
                pool.map(self.get_device_result, process_args)
                pool.close()
                pool.join()
            else:
                results = [self.get_results(payload, device) for device in self.devices]
            return {
                "success": all(result["success"] for result in results),
                "runtime": self.runtime,
            }

    def create_result(self, results, device=None):
        self.success = results["success"]
        result_kw = {
            "run": self,
            "result": results,
            "service": self.service_id,
            "parent_runtime": self.parent_runtime,
        }
        if self.workflow_id:
            result_kw["workflow"] = self.workflow_id
        if self.parent_device_id:
            result_kw["parent_device"] = self.parent_device_id
        if device:
            result_kw["device"] = device.id
        factory("result", **result_kw)

    def run_service_job(self, payload, device):
        args = (device,) if device else ()
        for retry in range(self.number_of_retries + 1):
            try:
                if retry:
                    self.log("error", f"RETRY n°{retry}", device)
                results = self.service.job(self, payload, *args)
                if device and (
                    getattr(self, "close_connection", False)
                    or self.runtime == self.parent_runtime
                ):
                    self.close_device_connection(device)
                self.convert_result(results)
                if "success" not in results:
                    results["success"] = True
                try:
                    self.eval(
                        self.service.result_postprocessing, function="exec", **locals()
                    )
                except SystemExit:
                    pass
                if results["success"] and self.validation_method != "none":
                    self.validate_result(results, payload, device)
                if results["success"]:
                    return results
                elif retry < self.number_of_retries:
                    sleep(self.time_between_retries)
            except Exception:
                result = (
                    f"Running {self.service.type} '{self.service.name}'"
                    " raised the following exception:\n"
                    f"{chr(10).join(format_exc().splitlines())}\n\n"
                    "Run aborted..."
                )
                self.log("error", result, device)
                return {"success": False, "result": result}
        return results

    def get_results(self, payload, device=None):
        self.log("info", "STARTING", device)
        start = datetime.now().replace(microsecond=0)
        results = {"runtime": app.get_time(), "logs": []}
        try:
            if self.restart_run and self.service.type == "workflow":
                old_result = self.restart_run.result(
                    device=device.name if device else None
                )
                if old_result and "payload" in old_result.result:
                    payload.update(old_result["payload"])
            if self.service.iteration_values:
                targets_results = {}
                for target in self.eval(self.service.iteration_values, **locals()):
                    self.payload_helper(payload, self.iteration_variable_name, target)
                    targets_results[str(target)] = self.run_service_job(payload, device)
                results.update(
                    {
                        "result": targets_results,
                        "success": all(r["success"] for r in targets_results.values()),
                    }
                )
            else:
                results.update(self.run_service_job(payload, device))
        except Exception:
            results.update(
                {"success": False, "result": chr(10).join(format_exc().splitlines())}
            )
            self.log("error", chr(10).join(format_exc().splitlines()), device)
        results["duration"] = str(datetime.now().replace(microsecond=0) - start)
        if device and not self.parent_device:
            status = "success" if results["success"] else "failure"
            self.run_state["progress"]["device"][status] += 1
            self.run_state["summary"][status].append(device.name)
            self.create_result(results, device)
        Session.commit()
        self.log("info", "FINISHED", device)
        return results

    def log(self, severity, content, device=None):
        log = f"{app.get_time()} - {severity} - {self.service.name}"
        if device:
            log += f" - DEVICE {device.name}"
        log += f" : {content}"
        app.run_logs[self.parent_runtime].append(log)

    def build_notification(self, results):
        notification = {
            "Service": f"{self.service.name} ({self.service.type})",
            "Runtime": self.runtime,
            "Status": "PASS" if results["success"] else "FAILED",
        }
        if self.notification_header:
            notification["Header"] = self.notification_header
        if self.include_link_in_summary:
            address = app.config["app"]["address"]
            notification["Link"] = f"{address}/view_service_results/{self.id}"
        if results["summary"]:
            if results["summary"]["failure"]:
                notification["FAILED"] = results["summary"]["failure"]
            if results["summary"]["success"] and not self.display_only_failed_nodes:
                notification["PASSED"] = results["summary"]["success"]
        return notification

    def notify(self, results):
        self.log("info", f"Sending {self.send_notification_method} notification...")
        notification = self.build_notification(results)
        file_content = deepcopy(notification)
        if self.include_device_results:
            file_content["Device Results"] = {}
            for device in self.devices:
                device_result = fetch(
                    "result",
                    service_id=self.service_id,
                    parent_runtime=self.parent_runtime,
                    device_id=device.id,
                    allow_none=True,
                )
                if device_result:
                    file_content["Device Results"][device.name] = device_result.result
        try:
            if self.send_notification_method == "mail":
                filename = self.runtime.replace(".", "").replace(":", "")
                result = app.send_email(
                    f"{self.name} ({'PASS' if results['success'] else 'FAILED'})",
                    app.str_dict(notification),
                    recipients=self.mail_recipient,
                    filename=f"results-{filename}.txt",
                    file_content=app.str_dict(file_content),
                )
            elif self.send_notification_method == "slack":
                result = SlackClient(environ.get("SLACK_TOKEN")).api_call(
                    "chat.postMessage",
                    channel=app.config["slack"]["channel"],
                    text=notification,
                )
            else:
                result = post(
                    app.config["mattermost"]["url"],
                    verify=app.config["mattermost"]["verify_certificate"],
                    data=dumps(
                        {
                            "channel": app.config["mattermost"]["channel"],
                            "text": notification,
                        }
                    ),
                ).text
            results["notification"] = {"success": True, "result": result}
        except Exception:
            results["notification"] = {
                "success": False,
                "error": "\n".join(format_exc().splitlines()),
            }
        return results

    def get_credentials(self, device):
        return (
            app.get_user_credentials()
            if self.credentials == "user"
            else (device.username, device.password)
            if self.credentials == "device"
            else (
                self.sub(self.service.custom_username, locals()),
                self.sub(self.service.custom_password, locals()),
            )
        )

    def convert_result(self, result):
        if self.conversion_method == "none" or "result" not in result:
            return result
        try:
            if self.conversion_method == "text":
                result["result"] = str(result["result"])
            elif self.conversion_method == "json":
                result["result"] = loads(result["result"])
            elif self.conversion_method == "xml":
                result["result"] = parse(result["result"])
        except (ExpatError, JSONDecodeError) as e:
            result = {
                "success": False,
                "text_response": result,
                "error": f"Conversion to {self.conversion_method} failed",
                "exception": str(e),
            }
        return result

    def validate_result(self, results, payload, device):
        if self.validation_method == "text":
            match = self.sub(self.content_match, locals())
            str_result = str(results["result"])
            if self.delete_spaces_before_matching:
                match, str_result = map(self.space_deleter, (match, str_result))
            success = (
                self.content_match_regex
                and bool(search(match, str_result))
                or match in str_result
                and not self.content_match_regex
            )
        else:
            match = self.sub(self.dict_match, locals())
            success = self.match_dictionary(results["result"], match)
        results["success"] = not success if self.negative_logic else success
        results.update({"match": match, "negative_logic": self.negative_logic})

    def match_dictionary(self, result, match, first=True):
        if self.validation_method == "dict_equal":
            return result == self.dict_match
        else:
            match_copy = deepcopy(match) if first else match
            if isinstance(result, dict):
                for k, v in result.items():
                    if k in match_copy and match_copy[k] == v:
                        match_copy.pop(k)
                    else:
                        self.match_dictionary(v, match_copy, False)
            elif isinstance(result, list):
                for item in result:
                    self.match_dictionary(item, match_copy, False)
            return not match_copy

    def transfer_file(self, ssh_client, files):
        if self.protocol == "sftp":
            with SFTPClient.from_transport(
                ssh_client.get_transport(),
                window_size=self.window_size,
                max_packet_size=self.max_transfer_size,
            ) as sftp:
                for source, destination in files:
                    getattr(sftp, self.direction)(source, destination)
        else:
            with SCPClient(ssh_client.get_transport()) as scp:
                for source, destination in files:
                    getattr(scp, self.direction)(source, destination)

    def payload_helper(
        self, payload, name, value=None, device=None, section=None, operation="set"
    ):
        payload = payload.setdefault("variables", {})
        if device:
            payload = payload.setdefault("devices", {})
            payload = payload.setdefault(device, {})
        if section:
            payload = payload.setdefault(section, {})
        if value is not None:
            if operation == "set":
                payload[name] = value
            else:
                getattr(payload[name], operation)(value)
        else:
            if name not in payload:
                raise Exception(f"Payload Editor: {name} not found in {payload}.")
            return payload[name]

    def get_var(self, payload, name, device=None, **kwargs):
        return self.payload_helper(payload, name, device=device, **kwargs)

    def get_result(self, service_name, device=None, workflow=None):
        def filter_run(query, property):
            query = query.filter(
                models["run"].service.has(
                    getattr(models["service"], property) == service_name
                )
            )
            return query.all()

        def recursive_search(run: "Run"):
            if not run:
                return None
            query = Session.query(models["run"]).filter(
                models["run"].parent_runtime == run.parent_runtime
            )
            if workflow or self.workflow:
                name = workflow or self.workflow.name
                query.filter(
                    models["run"].workflow.has(models["workflow"].name == name)
                )
            runs = filter_run(query, "scoped_name") or filter_run(query, "name")
            results = list(filter(None, [run.result(device) for run in runs]))
            if not results:
                return recursive_search(run.restart_run)
            else:
                return results.pop().result

        return recursive_search(self)

    def python_code_kwargs(_self, **locals):  # noqa: N805
        return {
            "config": app.config,
            "devices": _self.devices,
            "get_var": partial(_self.get_var, locals.get("payload", {})),
            "get_result": _self.get_result,
            "log": _self.log,
            "workflow": _self.workflow,
            "set_var": partial(_self.payload_helper, locals.get("payload", {})),
            "parent_device": _self.parent_device or locals.get("device"),
            **locals,
        }

    def eval(_self, query, function="eval", **locals):  # noqa: N805
        return builtins[function](query, _self.python_code_kwargs(**locals))

    def sub(self, input, variables):
        r = compile("{{(.*?)}}")

        def replace(match):
            return str(self.eval(match.group()[2:-2], **variables))

        def rec(input):
            if isinstance(input, str):
                return r.sub(replace, input)
            elif isinstance(input, list):
                return [rec(x) for x in input]
            elif isinstance(input, dict):
                return {rec(k): rec(v) for k, v in input.items()}
            else:
                return input

        return rec(input)

    def space_deleter(self, input):
        return "".join(input.split())

    def update_netmiko_connection(self, connection):
        for property in ("fast_cli", "timeout", "global_delay_factor"):
            service_value = getattr(self.service, property)
            if service_value:
                setattr(connection, property, service_value)
        try:
            if not hasattr(connection, "check_config_mode"):
                self.log("error", f"Netmiko 'check_config_mode' method is missing.")
                return
            mode = connection.check_config_mode()
            if mode and not self.config_mode:
                connection.exit_config_mode()
            elif self.config_mode and not mode:
                connection.config_mode()
        except Exception as exc:
            self.log("error", f"Failed to honor the config mode {exc}")
        return connection

    def netmiko_connection(self, device):
        connection = self.get_or_close_connection("netmiko", device)
        if connection:
            self.log("info", "Using cached Netmiko connection", device)
            return self.update_netmiko_connection(connection)
        self.log("info", "Opening new Netmiko connection", device)
        username, password = self.get_credentials(device)
        driver = device.netmiko_driver if self.use_device_driver else self.driver
        netmiko_connection = ConnectHandler(
            device_type=driver,
            ip=device.ip_address,
            port=device.port,
            username=username,
            password=password,
            secret=device.enable_password,
            fast_cli=self.fast_cli,
            timeout=self.timeout,
            global_delay_factor=self.global_delay_factor,
        )
        if self.enable_mode:
            netmiko_connection.enable()
        if self.config_mode:
            netmiko_connection.config_mode()
        app.connections_cache["netmiko"][self.parent_runtime][
            device.name
        ] = netmiko_connection
        return netmiko_connection

    def napalm_connection(self, device):
        connection = self.get_or_close_connection("napalm", device)
        if connection:
            self.log("info", "Using cached NAPALM connection", device)
            return connection
        self.log("info", "Opening new NAPALM connection", device)
        username, password = self.get_credentials(device)
        optional_args = self.service.optional_args
        if not optional_args:
            optional_args = {}
        if "secret" not in optional_args:
            optional_args["secret"] = device.enable_password
        driver = get_network_driver(
            device.napalm_driver if self.use_device_driver else self.driver
        )
        napalm_connection = driver(
            hostname=device.ip_address,
            username=username,
            password=password,
            timeout=self.timeout,
            optional_args=optional_args,
        )
        napalm_connection.open()
        app.connections_cache["napalm"][self.parent_runtime][
            device.name
        ] = napalm_connection
        return napalm_connection

    def get_or_close_connection(self, library, device):
        connection = self.get_connection(library, device)
        if not connection:
            return
        if self.start_new_connection:
            return self.disconnect(library, device, connection)
        if library == "napalm":
            if connection.is_alive():
                return connection
            else:
                self.disconnect(library, device, connection)
        else:
            try:
                connection.find_prompt()
                return connection
            except Exception:
                self.disconnect(library, device, connection)

    def get_connection(self, library, device):
        cache = app.connections_cache[library].get(self.parent_runtime, {})
        return cache.get(device.name)

    def close_device_connection(self, device):
        for library in ("netmiko", "napalm"):
            connection = self.get_connection(library, device)
            if connection:
                self.disconnect(library, device, connection)

    def disconnect(self, library, device, connection):
        try:
            connection.disconnect() if library == "netmiko" else connection.close()
            app.connections_cache[library][self.parent_runtime].pop(device.name)
            self.log("info", f"Closed {library} connection", device)
        except Exception as exc:
            self.log(
                "error", f"Error while closing {library} connection ({exc})", device
            )

    def generate_yaml_file(self, path, device):
        data = {
            "last_failure": device.last_failure,
            "last_runtime": device.last_runtime,
            "last_update": device.last_update,
            "last_status": device.last_status,
        }
        with open(path / "data.yml", "w") as file:
            yaml.dump(data, file, default_flow_style=False)
