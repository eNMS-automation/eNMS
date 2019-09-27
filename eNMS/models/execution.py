from builtins import __dict__ as builtins
from copy import deepcopy
from functools import partial
from json import loads
from json.decoder import JSONDecodeError
from multiprocessing.pool import ThreadPool
from napalm import get_network_driver
from netmiko import ConnectHandler
from paramiko import SFTPClient
from re import compile, search
from scp import SCPClient
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from traceback import format_exc
from xmltodict import parse
from xml.parsers.expat import ExpatError

from eNMS import app
from eNMS.database import Session
from eNMS.database.dialect import Column, MutableDict, SmallString
from eNMS.database.functions import convert_value, factory, fetch, fetch_all
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
    workflow_device_id = Column(Integer, ForeignKey("device.id"))
    workflow_device = relationship("Device", foreign_keys="Run.workflow_device_id")
    parent_runtime = Column(SmallString)
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

    def __repr__(self):
        return f"{self.runtime} ({self.service_name} run by {self.creator})"

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        elif key in self.__dict__.get("properties", {}):
            service, value = (
                self.__dict__.get("service"),
                self.__dict__["properties"][key],
            )
            return convert_value(service.type, key, value, "id") if service else value
        elif self.__dict__.get("service_id"):
            return getattr(self.service, key)
        else:
            raise AttributeError

    def result(self, device=None):
        result = [r for r in self.results if r.device_name == device]
        return result.pop() if result else None

    def generate_row(self, table):
        service_type = "workflow" if self.service.type == "workflow" else "service"
        return [
            f"""<div class="btn-group" style="width: 100px;">
            <button type="button" class="btn btn-info btn-sm"
            onclick="showResultsPanel('{self.service.id}', '{self.name}',
            '{service_type}', '{self.runtime}')">Results</button>,
            <button type="button" class="btn btn-info btn-sm
            dropdown-toggle" data-toggle="dropdown">
              <span class="caret"></span>
            </button>
            <ul class="dropdown-menu" role="menu"><li><a href="#" onclick="
              showLogsPanel({self.service.row_properties}, '{self.runtime}')">Logs</a></li>
            </ul></div>"""
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

    def get_state(self, property):
        return app.run_db[self.runtime].get(property)

    def set_state(self, **kwargs):
        app.run_db[self.runtime].update(**kwargs)
        if self.workflow:
            app.run_db[self.parent_runtime]["services"][self.service.id].update(
                **kwargs
            )
            if "success" in kwargs:
                key = "passed" if kwargs["success"] else "failed"
                app.run_db[self.parent_runtime]["progress"][key] += 1

    @property
    def stop(self):
        return self.get_state("stop") or app.run_db[self.parent_runtime].get("stop")

    def compute_devices(self, payload):
        if self.service.python_query:
            values = self.eval(self.service.python_query, **locals())
            devices, not_found = [], []
            if isinstance(values, str):
                values = [values]
            for value in values:
                device = fetch(
                    "device",
                    allow_none=True,
                    **{self.service.query_property_type: value},
                )
                if device:
                    devices.append(device)
                else:
                    not_found.append(value)
            if not_found:
                raise Exception(f"Python query invalid targets: {', '.join(not_found)}")
        else:
            devices = set(self.devices)
            for pool in self.pools:
                devices |= set(pool.devices)
        self.set_state(number_of_targets=len(devices))
        return devices

    def run(self, payload=None):
        try:
            if self.service.type == "workflow":
                self.service.init_state(self)
            self.log("info", f"{self.service.type} {self.service.name}: Starting")
            self.set_state(status="Running", type=self.service.type)
            app.service_db[self.service.id]["runs"] += 1
            Session.commit()
            payload = payload or self.service.initial_payload
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
            self.close_connection_cache()
            self.status = "Aborted" if self.stop else "Completed"
            self.set_state(status=self.status, success=results["success"])
            app.service_db[self.service.id]["runs"] -= 1
            results["endtime"] = self.endtime = app.get_time()
            results["logs"] = app.run_logs.pop(self.runtime)
            self.state = app.run_db.pop(self.runtime)
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
        print("ooo"*100)
        return results

    @staticmethod
    def get_device_result(args):
        device = fetch("device", id=args[0])
        run = fetch("run", runtime=args[1])
        device_result = run.get_results(args[2], device)
        with args[3]:
            args[4][device.name] = device_result

    def device_run(self, payload):
        self.set_state(completed=0, failed=0)
        devices, success = self.compute_devices(payload), True
        if not devices:
            result = self.get_results(payload)
            return self.create_result(result)
        else:
            if self.multiprocessing:
                device_results = {}
                thread_lock = Lock()
                processes = min(len(devices), self.max_processes)
                process_args = [
                    (device.id, self.runtime, payload, thread_lock, device_results)
                    for device in devices
                ]
                pool = ThreadPool(processes=processes)
                pool.map(self.get_device_result, process_args)
                pool.close()
                pool.join()
            else:
                device_results = {
                    device.name: self.get_results(payload, device) for device in devices
                }
            for device_name, r in deepcopy(device_results).items():
                self.create_result(r, fetch("device", name=device_name))
                if not r["success"]:
                    success = False
            return {
                "success": success,
                "runtime": self.runtime,
            }

    def create_result(self, results, device=None):
        self.success = results["success"]
        result_kw = {"run": self, "result": results, "service": self.service_id}
        if self.workflow_id:
            result_kw["workflow"] = self.workflow_id
        if device:
            result_kw["device"] = device.id
        factory("result", **result_kw)
        return results

    def get_results(self, payload, *args):
        results = {"runtime": app.get_time(), "logs": []}
        try:
            if self.service.iteration_values:
                targets_results = {}
                for target in self.eval(self.service.iteration_values, **locals()):
                    self.payload_helper(payload, self.iteration_variable_name, target)
                    targets_results[target] = self.service.job(self, payload, *args)
                results.update(
                    {
                        "results": targets_results,
                        "success": all(r["success"] for r in targets_results.values()),
                    }
                )
            else:
                results.update(self.service.job(self, payload, *args))
        except Exception:
            results.update(
                {"success": False, "result": chr(10).join(format_exc().splitlines())}
            )
        self.eval(self.service.result_postprocessing, function="exec", **locals())
        results["endtime"] = app.get_time()
        completed, failed = self.get_state("completed"), self.get_state("failed")
        self.set_state(failed=failed + 1 - results["success"], completed=completed + 1)
        return results

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

    def netmiko_connection(self, device):
        if self.parent_runtime in app.connections_cache["netmiko"]:
            parent_connection = app.connections_cache["netmiko"].get(
                self.parent_runtime
            )
            if parent_connection and device.name in parent_connection:
                if self.service.start_new_connection:
                    parent_connection.pop(device.name).disconnect()
                else:
                    connection = parent_connection[device.name]
                    try:
                        connection.find_prompt()
                        for property in ("fast_cli", "timeout", "global_delay_factor"):
                            service_value = getattr(self.service, property)
                            if service_value:
                                setattr(connection, property, service_value)
                        try:
                            mode = connection.check_enable_mode()
                            if mode and not self.privileged_mode:
                                connection.exit_enable_mode()
                            elif self.privileged_mode and not mode:
                                connection.enable()
                        except Exception as exc:
                            self.log("error", f"Failed to honor the enable mode {exc}")
                        return connection
                    except (OSError, ValueError):
                        self.disconnect("netmiko", device, connection)
                        parent_connection.pop(device.name)
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
        if self.privileged_mode:
            netmiko_connection.enable()
        app.connections_cache["netmiko"][self.parent_runtime][
            device.name
        ] = netmiko_connection
        return netmiko_connection

    def napalm_connection(self, device):
        if self.parent_runtime in app.connections_cache["napalm"]:
            parent_connection = app.connections_cache["napalm"].get(self.parent_runtime)
            if parent_connection and device.name in parent_connection:
                if (
                    self.service.start_new_connection
                    or not parent_connection[device.name].is_alive()
                ):
                    parent_connection.pop(device.name).close()
                else:
                    return parent_connection[device.name]
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
            optional_args=optional_args,
        )
        napalm_connection.open()
        app.connections_cache["napalm"][self.parent_runtime][
            device.name
        ] = napalm_connection
        return napalm_connection

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
        try:
            if self.conversion_method == "text":
                result = str(result)
            elif self.conversion_method == "json":
                result = loads(result)
            elif self.conversion_method == "xml":
                result = parse(result)
        except (ExpatError, JSONDecodeError) as e:
            result = {
                "success": False,
                "text_response": result,
                "error": f"Conversion to {self.conversion_method} failed",
                "exception": str(e),
            }
        return result

    def match_content(self, result, match):
        if getattr(self, "validation_method", "text") == "text":
            result = str(result)
            assert isinstance(match, str)
            if self.delete_spaces_before_matching:
                match, result = map(self.space_deleter, (match, result))
            success = (
                self.content_match_regex
                and bool(search(match, result))
                or match in result
                and not self.content_match_regex
            )
        else:
            assert isinstance(match, dict)
            success = self.match_dictionary(result, match)
        return success if not self.negative_logic else not success

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
            "workflow_device": _self.workflow_device,
            **locals,
        }

    def eval(_self, query, function="eval", **locals):  # noqa: N805
        try:
            return builtins[function](query, _self.python_code_kwargs(**locals))
        except Exception as exc:
            raise Exception(
                "Python Query / Variable Substitution Failure."
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

    @property
    def name(self):
        return repr(self)

    def close_connection_cache(self):
        pool = ThreadPool(30)
        for library in ("netmiko", "napalm"):
            connections = app.connections_cache[library].pop(self.runtime, None)
            if not connections:
                continue
            for connection in connections.items():
                pool.apply_async(self.disconnect, (library, *connection))
        pool.close()
        pool.join()

    def disconnect(self, library, device, connection):
        try:
            connection.disconnect() if library == "netmiko" else connection.close()
            self.log("info", f"Closed {library} Connection to {device}")
        except Exception as exc:
            self.log(
                "error", f"{library} Connection to {device} couldn't be closed ({exc})"
            )
