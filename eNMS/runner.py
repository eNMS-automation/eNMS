from builtins import __dict__ as builtins
from copy import deepcopy
from datetime import datetime
from functools import partial
from importlib import __import__ as importlib_import
from io import BytesIO, StringIO
from jinja2 import Template
from json import dump, load, loads
from json.decoder import JSONDecodeError
from multiprocessing.pool import ThreadPool
from napalm import get_network_driver
from ncclient import manager
from netmiko import ConnectHandler
from operator import attrgetter
from os import getenv
from paramiko import AutoAddPolicy, RSAKey, SFTPClient, SSHClient
from re import compile, search
from requests import post
from scp import SCPClient
from sys import getsizeof
from threading import Thread
from time import sleep
from traceback import format_exc
from types import GeneratorType
from warnings import warn
from xmltodict import parse
from xml.parsers.expat import ExpatError

try:
    from scrapli import Scrapli
    from scrapli_netconf.driver import NetconfDriver
except ImportError as exc:
    warn(f"Couldn't import scrapli module ({exc})")

try:
    from slack_sdk import WebClient
except ImportError as exc:
    warn(f"Couldn't import slack_sdk module ({exc})")

from eNMS.database import db
from eNMS.environment import env
from eNMS.variables import vs


class Runner:
    def __init__(self, run, **kwargs):
        self.parameterized_run = False
        self.is_main_run = kwargs.pop("is_main_run", False)
        self.iteration_run = False
        self.workflow = None
        self.workflow_run_method = None
        self.parent_device = None
        self.run = run
        self.creator = self.run.creator
        self.start_services = []
        self.parent_runtime = kwargs.get("parent_runtime")
        self.runtime = self.parent_runtime if self.is_main_run else vs.get_time()
        self.has_result = False
        vs.run_instances[self.runtime] = self
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.in_process = False if self.is_main_run else run.in_process
        device_progress = "iteration_device" if self.iteration_run else "device"
        self.progress_key = f"progress/{device_progress}"
        self.is_admin_run = db.fetch("user", name=self.creator).is_admin
        self.main_run = db.fetch("run", runtime=self.parent_runtime)
        if not self.is_main_run:
            self.path = f"{run.path}>{self.service.id}"
        db.session.commit()
        self.start_run()
        vs.run_instances.pop(self.runtime)

    def __repr__(self):
        return f"{self.runtime}: SERVICE '{self.service}'"

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        elif set(self.__dict__) & {"service_id", "service"}:
            return getattr(self.service, key)
        else:
            raise AttributeError

    def get(self, property):
        if self.parameterized_run and property in self.payload["form"]:
            return self.payload["form"][property]
        else:
            return getattr(self, property)

    def get_target_property(self, property):
        if (
            self.is_main_run
            and self.restart_run
            and self.payload["targets"] != "Workflow"
        ):
            if property not in ("target_devices", "target_pools"):
                return None
            if self.payload["targets"] == "Manually defined":
                model = "pool" if property == "target_pools" else "device"
                return db.objectify(model, self.payload[f"restart_{model}s"])
            elif self.payload["targets"] == "Restart run":
                return getattr(self.restart_run, property)
        elif self.parameterized_run and property in self.payload["form"]:
            value = self.payload["form"][property]
            if property in ("target_devices", "target_pools"):
                model = "pool" if property == "target_pools" else "device"
                value = db.objectify(model, value)
            return value
        elif self.is_main_run and (
            self.main_run.target_devices or self.main_run.target_pools
        ):
            return getattr(self.main_run, property, [])
        elif self.workflow_run_method == "per_service_with_service_targets":
            return getattr(self.service, property)
        elif not self.is_main_run:
            return self.__dict__.get(property, [])
        else:
            return getattr(self.main_run.placeholder or self.service, property)

    @property
    def stop(self):
        if env.redis_queue:
            return bool(env.redis("get", f"stop/{self.parent_runtime}"))
        else:
            return vs.run_stop[self.parent_runtime]

    @property
    def progress(self):
        progress = self.main_run.get_state().get(self.path, {}).get("progress")
        try:
            progress = progress["device"]
            failure = int(progress.get("failure", 0))
            success = int(progress.get("success", 0))
            return f"{success + failure}/{progress['total']} ({failure} failed)"
        except (KeyError, TypeError):
            return "N/A"

    def compute_devices_from_query(_self, query, property, **locals):  # noqa: N805
        values = _self.eval(query, **locals)[0]
        devices, not_found = set(), []
        if isinstance(values, str):
            values = [values]
        for value in values:
            if isinstance(value, vs.models["device"]):
                device = value
            else:
                device = db.fetch("device", allow_none=True, **{property: value})
            if device:
                devices.add(device)
            else:
                not_found.append(value)
        if not_found:
            raise Exception(f"Device query invalid targets: {', '.join(not_found)}")
        return devices

    def compute_devices(self):
        devices = set(self.get_target_property("target_devices"))
        pools = self.get_target_property("target_pools")
        if self.get_target_property("device_query"):
            devices |= self.compute_devices_from_query(
                self.get_target_property("device_query"),
                self.get_target_property("device_query_property"),
            )
        if self.is_main_run:
            self.main_run.target_devices = list(devices)
            self.main_run.target_pools = list(pools)
        for pool in pools:
            if self.update_target_pools:
                pool.compute_pool()
            devices |= set(pool.devices)
        restricted_devices = set(
            device
            for device in devices
            if device.id not in vs.run_targets[self.parent_runtime]
        )
        if restricted_devices:
            result = (
                f"Error 403: User '{self.creator}' is not allowed to use these"
                f" devices as targets: {', '.join(map(str, restricted_devices))}"
            )
            self.log("info", result, logger="security")
        return list(devices - restricted_devices)

    def init_state(self):
        if not env.redis_queue:
            if vs.run_states[self.parent_runtime].get(self.path):
                return
            vs.run_states[self.parent_runtime][self.path] = {}
        if getattr(self.run, "placeholder", None):
            for property in ("id", "scoped_name", "type"):
                value = getattr(self.main_run.placeholder, property)
                self.write_state(f"placeholder/{property}", value)
        self.write_state("success", True)

    def write_state(self, path, value, method=None):
        if env.redis_queue:
            if isinstance(value, bool):
                value = str(value)
            env.redis(
                {None: "set", "append": "lpush", "increment": "incr"}[method],
                f"{self.parent_runtime}/state/{self.path}/{path}",
                value,
            )
        else:
            *keys, last = f"{self.parent_runtime}/{self.path}/{path}".split("/")
            store = vs.run_states
            for key in keys:
                store = store.setdefault(key, {})
            if not method:
                store[last] = value
            elif method == "increment":
                store.setdefault(last, 0)
                store[last] += value
            else:
                store.setdefault(last, []).append(value)

    def start_run(self):
        self.init_state()
        self.write_state("status", "Running")
        start = datetime.now().replace(microsecond=0)
        results = {"runtime": self.runtime, "success": True}
        try:
            vs.service_run_count[self.service.id] += 1
            results.update(self.device_run())
        except Exception:
            result = "\n".join(format_exc().splitlines())
            self.log("error", result)
            results.update({"success": False, "result": result})
        finally:
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                error = "\n".join(format_exc().splitlines())
                self.log("error", error)
                results.update({"success": False, "error": error})
            if self.update_pools_after_running:
                for pool in db.fetch_all("pool"):
                    pool.compute_pool()
            report = self.generate_report(results) if self.service.report else ""
            if self.get("send_notification"):
                try:
                    results = self.notify(results, report)
                except Exception:
                    error = "\n".join(format_exc().splitlines())
                    self.log("error", f"Notification error: {error}")
                    results["notification"] = {"success": False, "error": error}
            vs.service_run_count[self.service.id] -= 1
            if not vs.service_run_count[self.id]:
                self.service.status = "Idle"
            now = datetime.now().replace(microsecond=0)
            results["duration"] = str(now - start)
            if self.is_main_run:
                state = self.main_run.get_state()
                status = "Aborted" if self.stop else "Completed"
                self.main_run.state = state
                self.main_run.duration = results["duration"]
                self.main_run.status = state["status"] = status
                self.success = results["success"]
                self.close_remaining_connections()
            if self.main_run.task and not (
                self.main_run.task.frequency or self.main_run.task.crontab_expression
            ):
                self.main_run.task.is_active = False
            results["properties"] = self.service.get_properties(exclude=["positions"])
            results["trigger"] = self.main_run.trigger
            must_have_results = not self.has_result and not self.iteration_devices
            if self.is_main_run or len(self.target_devices) > 1 or must_have_results:
                results = self.create_result(results, run_result=self.is_main_run)
            if env.redis_queue and self.is_main_run:
                runtime_keys = env.redis("keys", f"{self.parent_runtime}/*") or []
                env.redis("delete", *runtime_keys)
            vs.custom.run_post_processing(self, results)

        self.results = results

    def make_json_compliant(self, input):
        def rec(value):
            if isinstance(value, dict):
                return {key: rec(value[key]) for key in list(value)}
            elif isinstance(value, list):
                return list(map(rec, value))
            elif not isinstance(
                value, (int, str, bool, float, None.__class__)
            ) or value in (float("inf"), float("-inf")):
                self.log("info", f"Converting {value} to string")
                return str(value)
            else:
                return value

        try:
            return rec(input)
        except Exception:
            log = f"Payload conversion to JSON failed:\n{format_exc()}"
            self.log("error", log)
            return {"error": log}

    @staticmethod
    def get_device_result(args):
        device_id, runtime, results = args
        device = db.fetch("device", id=device_id)
        run = vs.run_instances[runtime]
        results.append(run.get_results(device))

    def device_iteration(self, device):
        derived_devices = self.compute_devices_from_query(
            self.service.iteration_devices,
            self.service.iteration_devices_property,
            **locals(),
        )
        return Runner(
            self.run,
            iteration_run=True,
            payload=self.payload,
            service=self.service,
            target_devices=derived_devices,
            workflow=self.workflow,
            parent_device=device,
            restart_run=self.restart_run,
            parent=self,
            parent_runtime=self.parent_runtime,
        ).results["success"]

    def device_run(self):
        self.target_devices = self.compute_devices()
        summary = {"failure": [], "success": [], "discard": []}
        if self.iteration_devices and not self.iteration_run:
            if not self.workflow:
                result = "Device iteration not allowed outside of a workflow"
                return {"success": False, "result": result, "runtime": self.runtime}
            self.write_state(
                "progress/device/total", len(self.target_devices), "increment"
            )
            for device in self.target_devices:
                key = "success" if self.device_iteration(device) else "failure"
                self.write_state(f"progress/device/{key}", 1, "increment")
                summary[key].append(device.name)
            return {
                "success": not summary["failure"],
                "summary": summary,
                "runtime": self.runtime,
            }
        self.write_state(
            f"{self.progress_key}/total", len(self.target_devices), "increment"
        )
        non_skipped_targets, skipped_targets, results = [], [], []
        skip_service = self.skip.get(getattr(self.workflow, "name", None))
        if skip_service:
            self.write_state("status", "Skipped")
        if (
            self.run_method == "once"
            and not self.target_devices
            and self.eval(self.skip_query, **locals())[0]
        ):
            self.write_state("status", "Skipped")
            return {
                "success": self.skip_value == "success",
                "result": "skipped",
                "runtime": self.runtime,
            }
        for device in self.target_devices:
            skip_device = skip_service
            if not skip_service and self.skip_query:
                skip_device = self.eval(self.skip_query, **locals())[0]
            if skip_device:
                if device:
                    self.write_state(f"{self.progress_key}/skipped", 1, "increment")
                if self.skip_value == "discard":
                    continue
                device_results = {
                    "device_target": getattr(device, "name", None),
                    "runtime": vs.get_time(),
                    "result": "skipped",
                    "duration": "0:00:00",
                    "success": self.skip_value == "success",
                }
                skipped_targets.append(device.name)
                self.create_result(device_results, device, commit=False)
                results.append(device_results)
            else:
                non_skipped_targets.append(device)
        self.target_devices = non_skipped_targets
        if self.run_method != "per_device":
            results = self.get_results()
            if "summary" not in results:
                summary_key = "success" if results["success"] else "failure"
                device_names = [device.name for device in self.target_devices]
                summary[summary_key].extend(device_names)
                results["summary"] = summary
            for key in ("success", "failure"):
                self.write_state(
                    f"{self.progress_key}/{key}",
                    len(results["summary"][key]),
                    "increment",
                )
            summary[self.skip_value].extend(skipped_targets)
            return results
        else:
            if self.is_main_run and not self.target_devices:
                error = (
                    "The service 'Run method' is set to 'Per device' mode, "
                    "but no targets have been selected (in Step 3 > Targets)"
                )
                self.log("error", error)
                return {"success": False, "runtime": self.runtime, "result": error}
            if (
                self.get("multiprocessing")
                and len(non_skipped_targets) > 1
                and not self.in_process
                and not self.iteration_run
            ):
                processes = min(len(non_skipped_targets), self.get("max_processes"))
                process_args = [
                    (device.id, self.runtime, results) for device in non_skipped_targets
                ]
                self.log("info", f"Starting a pool of {processes} threads")
                self.in_process = True
                with ThreadPool(processes=processes) as pool:
                    pool.map(self.get_device_result, process_args)
                self.in_process = False
            else:
                results.extend(
                    [
                        self.get_results(device, commit=False)
                        for device in non_skipped_targets
                    ]
                )
            for result in results:
                key = "success" if result["success"] else "failure"
                summary[key].append(result["device_target"])
            return {
                "summary": summary,
                "success": all(result["success"] for result in results if result),
                "runtime": self.runtime,
            }

    def check_size_before_commit(self, data, data_type):
        column_type = "pickletype" if data_type == "result" else "large_string"
        data_size = getsizeof(str(data))
        max_allowed_size = vs.database["columns"]["length"][column_type]
        if data_size >= max_allowed_size:
            logs = (
                f"The {data_type} is too large to be committed to the database\n"
                f"Size: {data_size}B\nMaximum Allowed Size: {max_allowed_size}B"
            )
            self.log("critical", logs)
            raise Exception(f"{data_type.capitalize()} Data Overflow")

    def create_result(self, results, device=None, commit=True, run_result=False):
        self.success = results["success"]
        result_kw = {
            "parent_runtime": self.parent_runtime,
            "parent_service_id": self.main_run.service.id,
            "run_id": self.main_run.id,
            "service": self.service.id,
            "labels": self.main_run.labels,
            "creator": self.main_run.creator,
        }
        if self.workflow:
            result_kw["workflow"] = self.workflow.id
        if self.parent_device:
            result_kw["parent_device"] = self.parent_device.id
        if device:
            result_kw["device"] = device.id
        if self.is_main_run and not device:
            self.payload = self.make_json_compliant(self.payload)
            results["payload"] = self.payload
            services = list(vs.run_logs.get(self.parent_runtime, []))
            for service_id in services:
                logs = env.log_queue(self.parent_runtime, service_id, mode="get")
                content = "\n".join(logs or [])
                self.check_size_before_commit(content, "log")
                db.factory(
                    "service_log",
                    runtime=self.parent_runtime,
                    service=service_id,
                    content=content,
                )
            if self.main_run.trigger == "REST API":
                results["devices"] = {}
                for result in self.main_run.results:
                    if not result.device:
                        continue
                    results["devices"][result.device.name] = result.result
        else:
            results.pop("payload", None)
        create_failed_results = self.disable_result_creation and not self.success
        results = self.make_json_compliant(results)
        self.check_size_before_commit(results, "result")
        if not self.disable_result_creation or create_failed_results or run_result:
            self.has_result = True
            try:
                db.factory("result", result=results, commit=commit, **result_kw)
            except Exception:
                self.log("critical", f"Failed to commit result:\n{format_exc()}")
                db.session.rollback()
        return results

    def run_service_job(self, device):
        args = (device,) if device else ()
        retries, total_retries = self.number_of_retries + 1, 0
        while retries and total_retries < self.max_number_of_retries:
            if self.stop:
                self.log("error", f"ABORTING {device.name} (STOP)")
                return {"success": False, "result": "Aborted"}
            retries -= 1
            total_retries += 1
            try:
                if self.number_of_retries - retries:
                    retry = self.number_of_retries - retries
                    self.log("error", f"RETRY n°{retry}", device)
                if self.service.preprocessing:
                    try:
                        self.eval(
                            self.service.preprocessing, function="exec", **locals()
                        )
                    except SystemExit:
                        pass
                try:
                    results = self.service.job(self, *args)
                except Exception:
                    result = "\n".join(format_exc().splitlines())
                    self.log("error", result, device)
                    results = {"success": False, "result": result}
                results = self.convert_result(results)
                if "success" not in results:
                    results["success"] = True
                if self.service.postprocessing:
                    if (
                        self.postprocessing_mode == "always"
                        or self.postprocessing_mode == "failure"
                        and not results["success"]
                        or self.postprocessing_mode == "success"
                        and results["success"]
                    ):
                        try:
                            _, exec_variables = self.eval(
                                self.service.postprocessing, function="exec", **locals()
                            )
                            if isinstance(exec_variables.get("retries"), int):
                                retries = exec_variables["retries"]
                        except SystemExit:
                            pass
                    else:
                        log = (
                            "Postprocessing was skipped as it is set to "
                            f"{self.postprocessing_mode} only, and the service "
                            f"{'passed' if results['success'] else 'failed'})"
                        )
                        self.log("warning", log, device)
                run_validation = (
                    self.validation_condition == "always"
                    or self.validation_condition == "failure"
                    and not results["success"]
                    or self.validation_condition == "success"
                    and results["success"]
                )
                if run_validation:
                    section = self.eval(self.validation_section, results=results)[0]
                    results.update(self.validate_result(section, device))
                    if self.negative_logic:
                        results["success"] = not results["success"]
                if results["success"]:
                    return results
                elif retries:
                    sleep(self.time_between_retries)
            except Exception:
                result = "\n".join(format_exc().splitlines())
                self.log("error", result, device)
                results = {"success": False, "result": result}
        return results

    def get_results(self, device=None, commit=True):
        self.log("info", "STARTING", device)
        start = datetime.now().replace(microsecond=0)
        results = {"device_target": getattr(device, "name", None)}
        if self.stop:
            return {"success": False, **results}
        try:
            if self.service.iteration_values:
                targets_results = {}
                targets = self.eval(self.service.iteration_values, **locals())[0]
                if not isinstance(targets, dict):
                    if isinstance(targets, (GeneratorType, map, filter)):
                        targets = list(targets)
                    targets = dict(zip(map(str, targets), targets))
                for target_name, target_value in targets.items():
                    self.payload_helper(
                        self.iteration_variable_name,
                        target_value,
                        device=getattr(device, "name", None),
                    )
                    targets_results[target_name] = self.run_service_job(device)
                results.update(
                    {
                        "result": targets_results,
                        "success": all(
                            result["success"] for result in targets_results.values()
                        ),
                    }
                )
            else:
                results.update(self.run_service_job(device))
        except Exception:
            formatted_error = "\n".join(format_exc().splitlines())
            results.update({"success": False, "result": formatted_error})
            self.log("error", formatted_error, device)
        results["duration"] = str(datetime.now().replace(microsecond=0) - start)
        if device:
            if getattr(self, "close_connection", False) or self.is_main_run:
                self.close_device_connection(device.name)
            status = "success" if results["success"] else "failure"
            self.write_state(f"{self.progress_key}/{status}", 1, "increment")
            self.create_result(
                {"runtime": vs.get_time(), **results}, device, commit=commit
            )
        self.log("info", "FINISHED", device)
        if self.waiting_time:
            self.log("info", f"SLEEP {self.waiting_time} seconds...", device)
            sleep(self.waiting_time)
        if not results["success"]:
            self.write_state("success", False)
        return results

    def log(
        self,
        severity,
        log,
        device=None,
        change_log=False,
        logger=None,
        service_log=True,
        allow_disable=True,
    ):
        try:
            log_level = int(self.main_run.service.log_level)
        except Exception:
            log_level = 1
        if (
            logger != "security"
            and allow_disable
            and (log_level == -1 or severity not in vs.log_levels[log_level:])
        ):
            return
        if device:
            device_name = device if isinstance(device, str) else device.name
            log = f"DEVICE {device_name} - {log}"
        full_log = (
            f"RUNTIME {self.parent_runtime} - USER {self.creator} -"
            f" SERVICE '{self.service.name}' - {log}"
        )
        settings = env.log(
            severity, full_log, user=self.creator, change_log=change_log, logger=logger
        )
        if service_log or logger and settings.get("service_log"):
            run_log = (
                f"{vs.get_time()} - {severity} - USER {self.creator} -"
                f" SERVICE {self.service.scoped_name} - {log}"
            )
            env.log_queue(self.parent_runtime, self.service.id, run_log)
            if not self.is_main_run:
                env.log_queue(self.parent_runtime, self.main_run.service.id, run_log)

    def build_notification(self, results):
        notification = {
            "Service": f"{self.service.name} ({self.service.type})",
            "Runtime": self.runtime,
            "Status": "PASS" if results["success"] else "FAILED",
        }
        if "result" in results:
            notification["Results"] = results["result"]
        if self.notification_header:
            notification["Header"] = self.sub(self.notification_header, locals())
        if self.include_link_in_summary:
            run = f"{self.main_run.id}/{self.service.id}"
            notification["Link"] = f"{vs.server_url}/view_service_results/{run}"
        if "summary" in results:
            if results["summary"]["failure"]:
                notification["FAILED"] = results["summary"]["failure"]
            if results["summary"]["success"] and not self.display_only_failed_nodes:
                notification["PASSED"] = results["summary"]["success"]
        return notification

    def generate_report(self, results):
        try:
            report = ""
            if self.service.report:
                variables = {
                    "service": self.service,
                    "results": results,
                    **self.global_variables(),
                }
                if self.service.report_jinja2_template:
                    report = Template(self.service.report).render(variables)
                else:
                    report = self.sub(self.service.report, variables)
        except Exception:
            report = "\n".join(format_exc().splitlines())
            self.log("error", f"Failed to build report:\n{report}")
        if report:
            self.check_size_before_commit(report, "report")
            db.factory(
                "service_report",
                runtime=self.parent_runtime,
                service=self.service.id,
                content=report,
            )
        return report

    def notify(self, results, report):
        self.log("info", f"Sending {self.send_notification_method} notification...")
        notification = self.build_notification(results)
        file_content = deepcopy(notification)
        if self.include_device_results:
            file_content["Device Results"] = {}
            for device in self.target_devices:
                device_result = db.fetch(
                    "result",
                    service_id=self.service.id,
                    parent_runtime=self.parent_runtime,
                    device_id=device.id,
                    allow_none=True,
                )
                if device_result:
                    file_content["Device Results"][device.name] = device_result.result
        if self.send_notification_method == "mail":
            filename = self.runtime.replace(".", "").replace(":", "")
            status = "PASS" if results["success"] else "FAILED"
            content = report if self.email_report else vs.dict_to_string(notification)
            html_report = self.email_report and self.report_format == "html"
            result = env.send_email(
                f"{status}: {self.service.name}",
                content,
                recipients=self.sub(self.get("mail_recipient"), locals()),
                reply_to=self.reply_to,
                filename=f"results-{filename}.{'html' if html_report else 'txt'}",
                file_content=content,
                content_type="html" if html_report else "plain",
            )
        elif self.send_notification_method == "slack":
            result = WebClient(token=getenv("SLACK_TOKEN")).chat_postMessage(
                channel=f"#{vs.settings['slack']['channel']}",
                text=vs.dict_to_string(notification),
            )
        else:
            result = post(
                vs.settings["mattermost"]["url"],
                verify=vs.settings["mattermost"]["verify_certificate"],
                json={
                    "channel": vs.settings["mattermost"]["channel"],
                    "text": notification,
                },
            ).text
        results["notification"] = {"success": True, "result": result}
        return results

    def get_credentials(self, device, add_secret=True):
        result, credential_type = {}, self.main_run.service.credential_type
        if self.credentials == "object":
            credential = self.named_credential
        else:
            credential = db.get_credential(
                self.creator,
                device=device,
                credential_type=credential_type,
                optional=self.credentials != "device",
            )
        if add_secret and device and credential:
            log = f"Using '{credential.name}' credential for '{device.name}'"
            self.log("info", log)
            result["secret"] = env.get_password(credential.enable_password)
        if self.credentials in ("device", "object"):
            result["username"] = credential.username
            if credential.subtype == "password":
                result["password"] = env.get_password(credential.password)
            else:
                private_key = env.get_password(credential.private_key)
                result["pkey"] = RSAKey.from_private_key(StringIO(private_key))
        elif self.credentials == "user":
            user = db.fetch("user", name=self.creator)
            result["username"] = user.name
            result["password"] = env.get_password(user.password)
        else:
            result["username"] = self.sub(self.custom_username, locals())
            password = env.get_password(self.custom_password)
            substituted_password = self.sub(password, locals())
            if password != substituted_password:
                if substituted_password.startswith("b'"):
                    substituted_password = substituted_password[2:-1]
                password = env.get_password(substituted_password)
            result["password"] = password
        return result

    def convert_result(self, result):
        if self.conversion_method == "none" or "result" not in result:
            return result
        try:
            if self.conversion_method == "text":
                result["result"] = str(result["result"])
            elif self.conversion_method == "json":
                result["result"] = loads(result["result"])
            elif self.conversion_method == "xml":
                result["result"] = parse(result["result"], force_list=True)
        except (ExpatError, JSONDecodeError) as exc:
            result = {
                "success": False,
                "text_response": result,
                "error": f"Conversion to {self.conversion_method} failed",
                "exception": str(exc),
            }
        return result

    def validate_result(self, section, device):
        if self.validation_method == "text":
            match = self.sub(self.content_match, locals())
            str_section = str(section)
            if self.delete_spaces_before_matching:
                match, str_section = map(self.space_deleter, (match, str_section))
            success = (
                self.content_match_regex
                and bool(search(match, str_section))
                or match in str_section
                and not self.content_match_regex
            )
        else:
            match = self.sub(self.dict_match, locals())
            success = self.match_dictionary(section, match)
        validation = {"path": self.validation_section, "value": section, "match": match}
        return {"success": success, "validation": validation}

    def match_dictionary(self, result, match, first=True):
        if self.validation_method == "dict_equal":
            return result == self.dict_match
        else:
            copy = deepcopy(match) if first else match
            if isinstance(result, dict):
                for k, v in result.items():
                    if isinstance(copy.get(k), list) and isinstance(v, list):
                        for item in v:
                            try:
                                copy[k].remove(item)
                            except ValueError:
                                pass
                        pop_key = not copy[k]
                    else:
                        pop_key = k in copy and copy[k] == v
                    copy.pop(k) if pop_key else self.match_dictionary(v, copy, False)
            elif isinstance(result, list):
                for item in result:
                    self.match_dictionary(item, copy, False)
            return not copy

    def transfer_file(self, ssh_client, files):
        if self.protocol == "sftp":
            with SFTPClient.from_transport(
                ssh_client.get_transport(),
                window_size=self.window_size,
                max_packet_size=self.max_transfer_size,
            ) as sftp:
                sftp.get_channel().settimeout(self.timeout)
                for source, destination in files:
                    getattr(sftp, self.direction)(source, destination)
        else:
            with SCPClient(
                ssh_client.get_transport(), socket_timeout=self.timeout
            ) as scp:
                for source, destination in files:
                    getattr(scp, self.direction)(source, destination)

    def payload_helper(
        self,
        name,
        value=None,
        device=None,
        section=None,
        operation="__setitem__",
        allow_none=False,
        default=None,
    ):
        payload = self.payload.setdefault("variables", {})
        if device:
            payload = payload.setdefault("devices", {})
            payload = payload.setdefault(device, {})
        if section:
            payload = payload.setdefault(section, {})
        if value is None:
            value = default
        if operation in ("get", "__setitem__", "setdefault"):
            value = getattr(payload, operation)(name, value)
        else:
            getattr(payload[name], operation)(value)
        if operation == "get" and not allow_none and value is None:
            raise Exception(f"Payload Editor: {name} not found in {payload}.")
        else:
            return value

    def get_var(self, *args, **kwargs):
        return self.payload_helper(*args, operation="get", **kwargs)

    def get_result(self, service_name, device=None, workflow=None, all_matches=False):
        def filter_run(query, property):
            query = query.filter(
                vs.models["result"].service.has(
                    getattr(vs.models["service"], property) == service_name
                )
            )
            return query.all()

        def recursive_search(run):
            if not run:
                return None
            query = db.session.query(vs.models["result"]).filter(
                vs.models["result"].parent_runtime == run.runtime
            )
            if workflow:
                query = query.filter(
                    vs.models["result"].workflow.has(
                        vs.models["workflow"].name == workflow
                    )
                )
            if device:
                query = query.filter(
                    vs.models["result"].device.has(vs.models["device"].name == device)
                )
            results = filter_run(query, "scoped_name") or filter_run(query, "name")
            if not results:
                return recursive_search(run.restart_run)
            else:
                if all_matches:
                    return [result.result for result in results]
                else:
                    return results.pop().result

        return recursive_search(self.main_run)

    def get_all_results(self):
        return db.fetch_all("result", parent_runtime=self.parent_runtime)

    @staticmethod
    def _import(module, *args, **kwargs):
        if module in vs.settings["security"]["forbidden_python_libraries"]:
            raise ImportError(f"Module '{module}' is restricted.")
        return importlib_import(module, *args, **kwargs)

    def database_function(self, func, model, **kwargs):
        if model not in vs.automation["workflow"]["allowed_models"][func]:
            raise db.rbac_error(f"Use of '{func}' not allowed on {model}s.")
        kwargs["rbac"] = "edit"
        return getattr(db, func)(model, username=self.creator, **kwargs)

    def get_credential(self, **kwargs):
        credential = db.get_credential(self.creator, **kwargs)
        credential_dict = {"username": credential.username}
        if credential.subtype == "password":
            credential_dict["password"] = env.get_password(credential.password)
        else:
            private_key = env.get_password(credential.private_key)
            credential_dict["pkey"] = RSAKey.from_private_key(StringIO(private_key))
        credential_dict["secret"] = env.get_password(credential.enable_password)
        return credential_dict

    def global_variables(_self, **locals):  # noqa: N805
        payload, device = _self.payload, locals.get("device")
        variables = {**locals, **payload.get("form", {})}
        variables.update(payload.get("variables", {}))
        if device and "devices" in payload.get("variables", {}):
            variables.update(payload["variables"]["devices"].get(device.name, {}))
        variables.update(
            {
                "__builtins__": {**builtins, "__import__": _self._import},
                "delete": partial(_self.database_function, "delete"),
                "devices": _self.target_devices,
                "dict_to_string": vs.dict_to_string,
                "encrypt": env.encrypt_password,
                "factory": partial(_self.database_function, "factory"),
                "fetch": partial(_self.database_function, "fetch"),
                "fetch_all": partial(_self.database_function, "fetch_all"),
                "get_all_results": _self.get_all_results,
                "get_connection": _self.get_connection,
                "get_result": _self.get_result,
                "get_var": _self.get_var,
                "log": _self.log,
                "parent_device": _self.parent_device or device,
                "payload": _self.payload,
                "placeholder": _self.main_run.placeholder,
                "send_email": env.send_email,
                "server": {
                    "ip_address": vs.server_ip,
                    "name": vs.server,
                    "url": vs.server_url,
                },
                "set_var": _self.payload_helper,
                "username": _self.main_run.creator,
                "workflow": _self.workflow,
            }
        )
        if _self.is_admin_run:
            variables["get_credential"] = _self.get_credential
        return variables

    def eval(_self, query, function="eval", **locals):  # noqa: N805
        exec_variables = _self.global_variables(**locals)
        results = builtins[function](query, exec_variables) if query else ""
        return results, exec_variables

    def sub(self, input, variables):
        regex = compile("{{(.*?)}}")
        variables["payload"] = self.payload

        def replace(match):
            return str(self.eval(match.group()[2:-2], **variables)[0])

        def rec(input):
            if isinstance(input, str):
                return regex.sub(replace, input)
            elif isinstance(input, list):
                return [rec(item) for item in input]
            elif isinstance(input, dict):
                return {rec(key): rec(value) for key, value in input.items()}
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
            if not hasattr(connection, "check_enable_mode"):
                self.log("error", "Netmiko 'check_enable_mode' method is missing")
                return connection
            mode = connection.check_enable_mode()
            if mode and not self.enable_mode:
                connection.exit_enable_mode()
            elif self.enable_mode and not mode:
                connection.enable()
        except Exception as exc:
            self.log("error", f"Failed to honor the enable mode {exc}")
        try:
            if not hasattr(connection, "check_config_mode"):
                self.log("error", "Netmiko 'check_config_mode' method is missing")
                return connection
            mode = connection.check_config_mode()
            if mode and not self.config_mode:
                connection.exit_config_mode()
            elif self.config_mode and not mode:
                kwargs = {}
                if getattr(self, "config_mode_command", None):
                    kwargs["config_command"] = self.config_mode_command
                connection.config_mode(**kwargs)
        except Exception as exc:
            self.log("error", f"Failed to honor the config mode {exc}")
        return connection

    def netmiko_connection(self, device):
        connection = self.get_or_close_connection("netmiko", device.name)
        connection_name = f"Netmiko Connection '{self.connection_name}'"
        if connection:
            self.log("info", f"Using cached {connection_name}", device)
            return self.update_netmiko_connection(connection)
        driver = device.netmiko_driver if self.driver == "device" else self.driver
        self.log(
            "info",
            f"OPENING {connection_name} (driver: {driver})",
            device,
            change_log=False,
            logger="security",
        )
        sock = None
        if device.gateways:
            gateways = sorted(device.gateways, key=attrgetter("priority"), reverse=True)
            for gateway in gateways:
                try:
                    credentials = self.get_credentials(gateway, add_secret=False)
                    connection_log = f"Trying to establish connection to {gateway}"
                    self.log("info", connection_log, device, logger="security")
                    client = SSHClient()
                    client.set_missing_host_key_policy(AutoAddPolicy())
                    client.connect(
                        hostname=gateway.ip_address, port=gateway.port, **credentials
                    )
                    sock = client.get_transport().open_channel(
                        "direct-tcpip", (device.ip_address, device.port), ("", 0)
                    )
                    break
                except Exception:
                    error_log = f"Connection to {gateway} failed:\n{format_exc()}"
                    self.log("error", error_log, device)
        netmiko_connection = ConnectHandler(
            device_type=driver,
            ip=device.ip_address,
            port=device.port,
            fast_cli=self.fast_cli,
            timeout=self.timeout,
            global_delay_factor=self.global_delay_factor,
            session_log=BytesIO(),
            global_cmd_verify=False,
            sock=sock,
            **self.get_credentials(device),
        )
        if self.enable_mode:
            netmiko_connection.enable()
        if self.config_mode:
            kwargs = {}
            if getattr(self, "config_mode_command", None):
                kwargs["config_command"] = self.config_mode_command
            netmiko_connection.config_mode(**kwargs)
        vs.connections_cache["netmiko"][self.parent_runtime].setdefault(
            device.name, {}
        )[self.connection_name] = netmiko_connection
        return netmiko_connection

    def scrapli_connection(self, device):
        connection = self.get_or_close_connection("scrapli", device.name)
        connection_name = f"Scrapli Connection '{self.connection_name}'"
        if connection:
            self.log("info", f"Using cached {connection_name}", device)
            return connection
        self.log(
            "info",
            f"OPENING {connection_name}",
            device,
            change_log=False,
            logger="security",
        )
        credentials = self.get_credentials(device)
        is_netconf = self.service.type == "scrapli_netconf_service"
        connection_class, kwargs = NetconfDriver if is_netconf else Scrapli, {}
        if is_netconf:
            kwargs["strip_namespaces"] = self.strip_namespaces
        else:
            platform = device.scrapli_driver if self.driver == "device" else self.driver
            kwargs.update(
                {
                    "transport": self.transport,
                    "platform": platform,
                    "timeout_socket": self.timeout_socket,
                    "timeout_transport": self.timeout_transport,
                    "timeout_ops": self.timeout_ops,
                }
            )
        connection = connection_class(
            host=device.ip_address,
            auth_username=credentials["username"],
            auth_password=credentials["password"],
            **vs.automation["scrapli"]["connection_args"],
            **kwargs,
        )
        connection.open()
        vs.connections_cache["scrapli"][self.parent_runtime].setdefault(
            device.name, {}
        )[self.connection_name] = connection
        return connection

    def napalm_connection(self, device):
        connection = self.get_or_close_connection("napalm", device.name)
        connection_name = f"NAPALM Connection '{self.connection_name}'"
        if connection:
            self.log("info", f"Using cached {connection_name}", device)
            return connection
        self.log(
            "info",
            f"OPENING {connection_name}",
            device,
            change_log=False,
            logger="security",
        )
        credentials = self.get_credentials(device)
        optional_args = self.service.optional_args
        if not optional_args:
            optional_args = {}
        if "secret" not in optional_args:
            optional_args["secret"] = credentials.pop("secret", None)
        driver = get_network_driver(
            device.napalm_driver if self.driver == "device" else self.driver
        )
        napalm_connection = driver(
            hostname=device.ip_address,
            timeout=self.timeout,
            optional_args=optional_args,
            **credentials,
        )
        napalm_connection.open()
        vs.connections_cache["napalm"][self.parent_runtime].setdefault(device.name, {})[
            self.connection_name
        ] = napalm_connection
        return napalm_connection

    def ncclient_connection(self, device):
        connection = self.get_or_close_connection("ncclient", device.name)
        connection_name = f"NCClient Connection '{self.connection_name}'"
        if connection:
            self.log("info", f"Using cached {connection_name}", device)
            return connection
        self.log(
            "info",
            f"OPENING {connection_name}",
            device,
            change_log=False,
            logger="security",
        )
        credentials = self.get_credentials(device)
        ncclient_connection = manager.connect(
            host=device.ip_address,
            port=830,
            hostkey_verify=False,
            look_for_keys=False,
            device_params={"name": device.netconf_driver or "default"},
            username=credentials["username"],
            password=credentials["password"],
        )
        vs.connections_cache["ncclient"][self.parent_runtime].setdefault(
            device.name, {}
        )[self.connection_name] = ncclient_connection
        return ncclient_connection

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
        elif library == "ncclient":
            if connection.connected:
                return connection
            else:
                self.disconnect(library, device, connection)
        else:
            try:
                if library == "netmiko":
                    connection.find_prompt()
                else:
                    connection.get_prompt()
                return connection
            except Exception:
                self.disconnect(library, device, connection)

    def get_connection(self, library, device, name=None):
        cache = vs.connections_cache[library].get(self.parent_runtime, {})
        connection = name or getattr(self, "connection_name", "default")
        return cache.get(device, {}).get(connection)

    def close_device_connection(self, device):
        for library in ("netmiko", "napalm", "scrapli", "ncclient"):
            connection = self.get_connection(library, device)
            if connection:
                self.disconnect(library, device, connection)

    def close_remaining_connections(self):
        threads = []
        for library in ("netmiko", "napalm", "scrapli", "ncclient"):
            device_connections = vs.connections_cache[library][self.parent_runtime]
            for device, connections in list(device_connections.items()):
                for connection in list(connections.values()):
                    args = (library, device, connection)
                    thread = Thread(target=self.disconnect, args=args)
                    thread.start()
                    threads.append(thread)
        for thread in threads:
            thread.join()
        for library in ("netmiko", "napalm", "scrapli", "ncclient"):
            vs.connections_cache[library].pop(self.parent_runtime)

    def disconnect(self, library, device, connection):
        connection_name = getattr(self, "connection_name", "default")
        connection_log = f"{library} connection '{connection_name}'"
        try:
            if library == "netmiko":
                connection.disconnect()
            elif library == "ncclient":
                connection.close_session()
            else:
                connection.close()
            vs.connections_cache[library][self.parent_runtime][device].pop(
                connection_name
            )
            self.log("info", f"Closed {connection_log}", device)
        except Exception as exc:
            self.log("error", f"Error while closing {connection_log} ({exc})", device)

    def enter_remote_device(self, connection, device):
        if not getattr(self, "jump_on_connect", False):
            return
        connection.find_prompt()
        prompt = connection.base_prompt
        password = self.sub(env.get_password(self.jump_password), locals())
        commands = [
            (
                self.sub(self.jump_command, locals()),
                self.sub(self.expect_username_prompt, locals()),
            ),
            (
                self.sub(self.jump_username, locals()),
                self.sub(self.expect_password_prompt, locals()),
            ),
            (password, self.sub(self.expect_prompt, locals())),
        ]
        for send, expect in commands:
            if not send:
                continue
            pwd = send if password and send != password else "jump on connect password"
            self.log("info", f"Sent '{pwd}'" f", waiting for '{expect}'")
            connection.send_command(
                send,
                expect_string=expect,
                auto_find_prompt=False,
                strip_prompt=False,
                strip_command=True,
                max_loops=150,
            )
        return prompt

    def exit_remote_device(self, connection, prompt, device):
        if not getattr(self, "jump_on_connect", False):
            return
        exit_command = self.sub(self.exit_command, locals())
        self.log("info", f"Exit jump server with '{exit_command}'", device)
        connection.send_command(
            exit_command,
            expect_string=prompt or None,
            auto_find_prompt=True,
            strip_prompt=False,
            strip_command=True,
        )

    def update_configuration_properties(self, path, property, device):
        try:
            with open(path / "timestamps.json", "r") as file:
                data = load(file)
        except FileNotFoundError:
            data = {}
        data[property] = {
            timestamp: getattr(device, f"last_{property}_{timestamp}")
            for timestamp in vs.timestamps
        }
        with open(path / "timestamps.json", "w") as file:
            dump(data, file, indent=4)
