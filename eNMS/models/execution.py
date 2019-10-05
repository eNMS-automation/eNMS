from builtins import __dict__ as builtins
from collections import defaultdict
from copy import deepcopy
from functools import partial
from git import Repo
from git.exc import GitCommandError
from json import loads
from json.decoder import JSONDecodeError
from multiprocessing.pool import ThreadPool
from napalm import get_network_driver
from netmiko import ConnectHandler
from paramiko import SFTPClient
from pathlib import Path
from re import compile, search
from scp import SCPClient
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


class Result(AbstractBase):

    __tablename__ = type = "result"
    private = True
    id = Column(Integer, primary_key=True)
    success = Column(Boolean, default=False)
    runtime = Column(SmallString)
    endtime = Column(SmallString)
    result = Column(MutableDict)
    run_id = Column(Integer, ForeignKey("run.id"))
    run = relationship("Run", back_populates="results", foreign_keys="Result.run_id")
    parent_runtime = association_proxy("run", "parent_runtime")
    device_id = Column(Integer, ForeignKey("device.id"))
    device = relationship(
        "Device", back_populates="results", foreign_keys="Result.device_id"
    )
    device_name = association_proxy("device", "name")
    service_id = Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", foreign_keys="Result.service_id")
    service_name = association_proxy("service", "name")
    workflow_id = Column(Integer, ForeignKey("workflow.id"))
    workflow = relationship("Workflow", foreign_keys="Result.workflow_id")
    workflow_name = association_proxy("workflow", "name")

    def __repr__(self):
        return f"{self.service_name} on {self.device_name}"

    def __getitem__(self, key):
        return self.result[key]

    def __init__(self, **kwargs):
        self.success = kwargs["result"]["success"]
        self.runtime = kwargs["result"]["runtime"]
        self.endtime = kwargs["result"]["endtime"]
        super().__init__(**kwargs)

    def generate_row(self, table):
        return [
            f"""<button type="button" class="btn btn-info btn-sm"
            onclick="showResult('{self.id}')"></i>Results</a></button>""",
            f"""<input type="radio" name="v1" value="{self.id}"/>""",
            f"""<input type="radio" name="v2" value="{self.id}"/>""",
        ]


class Run(AbstractBase):

    __tablename__ = type = "run"
    private = True
    id = Column(Integer, primary_key=True)
    restart_run_id = Column(Integer, ForeignKey("run.id"))
    restart_run = relationship("Run", remote_side=[id])
    creator = Column(SmallString, default="admin")
    properties = Column(MutableDict)
    success = Column(Boolean, default=False)
    status = Column(SmallString, default="Running")
    runtime = Column(SmallString)
    endtime = Column(SmallString)
    parent_device_id = Column(Integer, ForeignKey("device.id"))
    parent_device = relationship("Device", foreign_keys="Run.parent_device_id")
    parent_runtime = Column(SmallString)
    devices = relationship("Device", secondary=run_device_table, back_populates="runs")
    pools = relationship("Pool", secondary=run_pool_table, back_populates="runs")
    service_id = Column(Integer, ForeignKey("service.id"))
    service = relationship(
        "Service", back_populates="runs", foreign_keys="Run.service_id"
    )
    service_name = association_proxy("service", "name")
    workflow_id = Column(Integer, ForeignKey("workflow.id"))
    workflow = relationship("Workflow", foreign_keys="Run.workflow_id")
    workflow_name = association_proxy("workflow", "name")
    task_id = Column(Integer, ForeignKey("task.id"))
    task = relationship("Task", foreign_keys="Run.task_id")
    state = Column(MutableDict)
    results = relationship("Result", back_populates="run", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        self.runtime = kwargs.get("runtime") or app.get_time()
        if not kwargs.get("parent_runtime"):
            self.parent_runtime = self.runtime
        super().__init__(**kwargs)

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

    def generate_row(self, table):
        return [
            f"""
            <ul class="pagination pagination-lg" style="margin: 0px; width: 100px">
          <li>
            <button type="button" class="btn btn-info"
            onclick="showResultsPanel({self.service.row_properties}, '{self.runtime}')"
              ><span class="glyphicon glyphicon-list-alt"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-info"
            onclick="showLogsPanel({self.service.row_properties}, '{self.runtime}')"
              ><span class="glyphicon glyphicon-list"></span
            ></button>
          </li>
        </ul>"""
        ]

    @property
    def progress(self):
        if self.status == "Running":
            progress = app.run_db[self.runtime]
            try:
                return (
                    f"{progress['completed']}/{progress['number_of_targets']}"
                    f" ({progress['failed']} failed)"
                )
            except KeyError:
                return "N/A"
        else:
            return "N/A"

    @property
    def run_state(self):
        if self.parent_runtime == self.runtime:
            return app.run_db[self.parent_runtime]
        else:
            return app.run_db[self.parent_runtime]["services"][self.service.id]

    @property
    def stop(self):
        return self.run_state["status"] == "stop"

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
        self.run_state["progress"]["device"]["total"] += len(devices)
        return devices

    def init_state(self):
        state = {
            "status": "Idle",
            "success": None,
            "progress": {"device": {"total": 0, "passed": 0, "failed": 0}},
            "attempt": 0,
            "waiting_time": {
                "total": self.service.waiting_time,
                "left": self.service.waiting_time,
            },
        }
        if self.service.type == "workflow":
            state.update({"edges": defaultdict(int), "services": defaultdict(dict)})
            state["progress"]["service"] = {
                "total": len(self.service.services),
                "passed": 0,
                "failed": 0,
                "skipped": 0,
            }
        if self.parent_runtime == self.runtime:
            if self.parent_runtime in app.run_db:
                return
            app.run_db[self.parent_runtime] = state
        else:
            service_states = app.run_db[self.parent_runtime]["services"]
            if self.service.id not in service_states:
                service_states[self.service.id] = state

    def run(self, payload=None):
        self.init_state()
        self.log("info", f"{self.service.type} {self.service.name}: Starting")
        self.run_state["status"] = "Running"
        if payload is None:
            payload = self.service.initial_payload
        try:
            app.service_db[self.service.id]["runs"] += 1
            Session.commit()
            if self.restart_run and self.service.type == "workflow":
                global_result = self.restart_run.result()
                if global_result:
                    payload["variables"] = global_result.result["results"].get(
                        "variables", {}
                    )
            results = self.device_run(payload)
        except Exception:
            result = (
                f"Running {self.service.type} '{self.service.name}'"
                " raised the following exception:\n"
                f"{chr(10).join(format_exc().splitlines())}\n\n"
                "Run aborted..."
            )
            self.log("error", result)
            results = {"success": False, "runtime": self.runtime, "results": result}
        finally:
            Session.commit()
            self.status = "Aborted" if self.stop else "Completed"
            self.run_state["status"] = self.status
            if self.run_state["success"] is not False:
                self.run_state["success"] = results["success"]
            app.service_db[self.service.id]["runs"] -= 1
            results["endtime"] = self.endtime = app.get_time()
            results["logs"] = app.run_logs.pop(self.runtime)
            if self.parent_runtime == self.runtime:
                self.state = app.run_db.pop(self.parent_runtime)
            if self.task and not self.task.frequency:
                self.task.is_active = False
            results["properties"] = {
                "run": self.properties,
                "service": self.service.get_properties(exclude=["positions"]),
            }
            self.create_result(results)
            self.log("info", f"{self.service.type} {self.service.name}: Finished")
            Session.commit()
        if not self.workflow and self.send_notification:
            self.notify(results)
        return results

    @staticmethod
    def get_device_result(args):
        device_id, runtime, payload, results = args
        device = fetch("device", id=device_id)
        run = fetch("run", runtime=runtime)
        results.append(run.get_results(payload, device))

    def device_iteration(self, payload, device):
        derived_devices = self.compute_devices_from_query(
            self.iteration_devices, self.iteration_devices_property, **locals()
        )
        for device in derived_devices:
            kwargs = {
                "service": self.service.id,
                "devices": [device.id for device in derived_devices],
                "workflow": self.workflow.id,
                "parent_device": device.id,
                "parent_runtime": self.parent_runtime,
                "restart_run": self.restart_run,
            }
            derived_run = factory("run", **kwargs)
            derived_run.properties = self.properties
            yield derived_run.run(payload)["success"]

    def device_run(self, payload):
        devices, success = self.compute_devices(payload), True
        if not devices:
            results = [self.get_results(payload)]
        else:
            if self.iteration_devices and not self.parent_device:
                success = all(
                    all(self.device_iteration(payload, device)) for device in devices
                )
                return {"success": success, "runtime": self.runtime}
            if self.multiprocessing:
                results = []
                processes = min(len(devices), self.max_processes)
                process_args = [
                    (device.id, self.runtime, payload, results) for device in devices
                ]
                pool = ThreadPool(processes=processes)
                pool.map(self.get_device_result, process_args)
                pool.close()
                pool.join()
            else:
                results = [self.get_results(payload, device) for device in devices]
        return {"success": all(results), "runtime": self.runtime}

    def create_result(self, results, device=None):
        self.success = results["success"]
        result_kw = {"run": self, "result": results, "service": self.service_id}
        if self.service.type == "workflow":
            result_kw["workflow"] = self.service_id
        elif self.workflow_id:
            result_kw["workflow"] = self.workflow_id
        if device:
            result_kw["device"] = device.id
        factory("result", **result_kw)
        return results

    def run_service_job(self, payload, device):
        args = (device,) if device else ()
        for i in range(self.number_of_retries + 1):
            try:
                results = self.service.job(self, payload, *args)
                if device and (
                    getattr(self, "close_connection", False)
                    or self.runtime == self.parent_runtime
                ):
                    print("ttt"*100, getattr(self, "close_connection", False), self.runtime == self.parent_runtime)
                    self.close_device_connection(device)
                self.convert_result(results)
                self.eval(
                    self.service.result_postprocessing, function="exec", **locals()
                )
                if results.get("success", True):
                    self.validate_result(results, payload, device)
                if results["success"]:
                    return results
                elif i < self.number_of_retries:
                    sleep(self.time_between_retries)
            except Exception:
                result = (
                    f"Running {self.service.type} '{self.service.name}'"
                    " raised the following exception:\n"
                    f"{chr(10).join(format_exc().splitlines())}\n\n"
                    "Run aborted..."
                )
                self.log("error", result)
                return {"success": False, "result": result}
        return results

    def get_results(self, payload, device=None):
        results = {"runtime": app.get_time(), "logs": []}
        try:
            if self.service.iteration_values:
                targets_results = {}
                for target in self.eval(self.service.iteration_values, **locals()):
                    self.payload_helper(payload, self.iteration_variable_name, target)
                    targets_results[target] = self.run_service_job(payload, device)
                results.update(
                    {
                        "results": targets_results,
                        "success": all(r["success"] for r in targets_results.values()),
                    }
                )
            else:
                results.update(self.run_service_job(payload, device))
        except Exception:
            results.update(
                {"success": False, "result": chr(10).join(format_exc().splitlines())}
            )
            self.log("error", chr(10).join(format_exc().splitlines()))
        results["endtime"] = app.get_time()
        if device:
            status = "passed" if results["success"] else "failed"
            self.run_state["progress"]["device"][status] += 1
        self.create_result(results, device)
        Session.commit()
        return results["success"]

    def log(self, severity, log):
        log = f"{app.get_time()} - {severity} - {log}"
        app.run_logs[self.runtime].append(log)
        if self.workflow:
            app.run_logs[self.parent_runtime].append(log)

    def run_notification(self, results):
        notification = self.notification_header.splitlines()
        if self.service.type == "workflow":
            return notification
        elif "devices" in results["results"] and not results["success"]:
            failed = "\n".join(
                device
                for device, device_results in results["results"]["devices"].items()
                if not device_results["success"]
            )
            notification.append(f"FAILED :\n{failed}")
            if not self.display_only_failed_nodes:
                passed = "\n".join(
                    device
                    for device, device_results in results["results"]["devices"].items()
                    if device_results["success"]
                )
                notification.append(f"\n\nPASS :\n{passed}")
        return notification

    def git_push(self, results):
        path_git_folder = Path.cwd() / "git" / "automation"
        with open(path_git_folder / self.name, "w") as file:
            file.write(app.str_dict(results))
        repo = Repo(str(path_git_folder))
        try:
            repo.git.add(A=True)
            repo.git.commit(m=f"Automatic commit ({self.name})")
        except GitCommandError:
            pass
        repo.remotes.origin.push()

    def notify(self, results):
        notification = [
            f"Service: {self.service.name} ({self.service.type})",
            f"Runtime: {self.runtime}",
            f'Status: {"PASS" if results["success"] else "FAILED"}',
        ]
        notification.extend(self.run_notification(results))
        if self.include_link_in_summary:
            notification.append(
                f"Results: {app.server_addr}/view_service_results/{self.id}"
            )
        if self.push_to_git:
            self.git_push(results)
        notification_payload = {
            "service": self.service.get_properties(),
            "results": results,
            "content": "\n\n".join(notification),
        }
        notification_run = factory(
            "run",
            **{"service": fetch("service", name=self.send_notification_method).id},
        )
        notification_run.run(notification_payload)

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

    def validate_result(self, result, payload, device):
        if self.validation_method == "none":
            if "success" not in result:
                result["success"] = True
            return result
        elif self.validation_method == "text":
            match = self.sub(self.content_match, locals())
            str_result = str(result)
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
            success = self.match_dictionary(result, match)
        result["success"] = not success if self.negative_logic else success
        result.update({"match": match, "negative_logic": self.negative_logic})

    def match_dictionary(self, result, match, first=True):
        if self.validation_method == "dict_equal":
            return result["result"] == self.dict_match
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

    def get_result(self, service, device=None):
        service_id = fetch("service", name=service).id

        def recursive_search(run: "Run"):
            if not run:
                return None
            runs = fetch(
                "run",
                allow_none=True,
                all_matches=True,
                parent_runtime=run.parent_runtime,
                service_id=service_id,
            )
            results = list(filter(None, [run.result(device) for run in runs]))
            if not results:
                return recursive_search(run.restart_run)
            else:
                return results.pop().result

        return recursive_search(self)

    def python_code_kwargs(_self, **locals):  # noqa: N805
        return {
            "config": app.custom_config,
            "get_var": partial(_self.get_var, locals.get("payload", {})),
            "get_result": _self.get_result,
            "workflow": _self.workflow,
            "set_var": partial(_self.payload_helper, locals.get("payload", {})),
            "parent_device": _self.parent_device,
            **locals,
        }

    def eval(_self, query, function="eval", **locals):  # noqa: N805
        try:
            return builtins[function](query, _self.python_code_kwargs(**locals))
        except Exception as exc:
            raise Exception(
                "Variable Substitution Failure."
                " Check that all variables are defined."
                " If you are using the 'device' variable, "
                f"check that the service has targets. ({str(exc)})"
            )

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
            return self.update_netmiko_connection(connection)
        username, password = self.get_credentials(device)
        driver = device.netmiko_driver if self.use_device_driver else self.driver
        netmiko_connection = ConnectHandler(
            device_type=driver,
            ip=device.ip_address,
            port=getattr(device, "port"),
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
            return connection
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
        if self.start_new_connection:
            return self.disconnect(library, device, connection)
        if library == "napalm":
            if connection.is_alive():
                return connection
            else:
                self.disconnect(library, device, connection)
        else:
            try:
                device_connection.find_prompt()
                return device_connection
            except Exception:
                self.disconnect(library, device, connection)

    def get_connection(self, library, device):
        connections = app.connections_cache[library].get(self.runtime)
        if not connections:
            connections = app.connections_cache[library].get(self.parent_runtime, {})
        if device.name not in connections:
            return
        return connections[device.name]

    def close_device_connection(self, device):
        for library in ("netmiko", "napalm"):
            connection = self.get_connection(library, device)
            if connection:
                self.disconnect(library, device, connection)

    def disconnect(self, library, device, connection):
        try:
            connection.disconnect() if library == "netmiko" else connection.close()
            self.log("info", f"Closed {library} Connection to {device}")
        except Exception as exc:
            self.log(
                "error", f"{library} Connection to {device} couldn't be closed ({exc})"
            )
