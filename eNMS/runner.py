from builtins import __dict__ as builtins
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from functools import partial
from importlib import __import__ as importlib_import
from io import BytesIO, StringIO
from jinja2 import Template
from json import dump, load, loads
from json.decoder import JSONDecodeError
from multiprocessing.pool import ThreadPool
from netmiko import ConnectHandler
from operator import attrgetter
from orjson import dumps as or_dumps, loads as or_loads, OPT_NON_STR_KEYS
from os import getenv
from paramiko import AutoAddPolicy, RSAKey, SFTPClient, SSHClient
from re import compile, search
from requests import post
from scp import SCPClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import load_only, selectinload
from sys import getsizeof
from time import sleep
from traceback import format_exc
from types import GeneratorType, SimpleNamespace
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

try:
    from ncclient import manager
except ImportError as exc:
    warn(f"Couldn't import ncclient module ({exc})")

try:
    from napalm import get_network_driver
except ImportError as exc:
    warn(f"Couldn't import napalm module ({exc})")

from eNMS.controller import controller
from eNMS.database import db
from eNMS.environment import env
from eNMS.variables import vs


class RunEngine:
    def __init__(self, run, **kwargs):
        self.kwargs = kwargs
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
        self.run_targets = []
        vs.run_instances[self.runtime] = self
        for key, value in kwargs.items():
            setattr(self, key, value)
        if self.service.soft_deleted:
            raise Exception(f"Service '{self.service}' is soft-deleted.")
        self.in_process = kwargs.get("in_process", getattr(run, "in_process", False))
        self.dry_run = getattr(run, "dry_run", False) or self.get("dry_run")
        device_progress = "iteration_device" if self.iteration_run else "device"
        self.progress_key = f"progress/{device_progress}"
        self.cache = {**run.cache, "service": self.get_service_properties()}
        self.main_run = run if self.is_main_run else run.main_run
        self.high_performance = self.cache["main_run_service"]["high_performance"]
        if env.redis_queue:
            env.redis("sadd", f"{self.parent_runtime}/services", self.service.id)
        else:
            vs.run_services[self.parent_runtime].add(self.service.id)
        if "in_process" in kwargs:
            self.path = run.path
        elif not self.is_main_run:
            self.path = f"{run.path}>{self.service.persistent_id}"
        if not self.high_performance:
            db.session.commit()

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        elif set(self.__dict__) & {"service_id", "service"}:
            return getattr(self.service, key)
        else:
            raise AttributeError

    def __repr__(self):
        return f"{self.runtime}: SERVICE '{self.service}'"

    def build_notification(self, results):
        notification = {
            "Service": f"{self.service.name} ({self.service.type})",
            "Server": vs.server_dict,
            "Runtime": self.runtime,
            "Status": "PASS" if results["success"] else "FAILED",
        }
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
        if "result" in results:
            notification["Results"] = results["result"]
        return notification

    def compute_targets_and_collect_results(self):
        if not self.run_targets:
            self.run_targets = self.compute_run_targets()
        allowed_devices, restricted_devices = [], []
        device_cache = self.cache["topology"]["name_to_dict"]["devices"]
        for device in self.run_targets:
            if device.id in vs.run_allowed_targets[self.parent_runtime]:
                allowed_devices.append(device)
                if self.high_performance and device.name not in device_cache:
                    device_namespace = SimpleNamespace(**device.get_properties())
                    device_cache[device.name] = device_namespace
            else:
                restricted_devices.append(device.name)
        if restricted_devices:
            result = (
                f"Error 403: User '{self.creator}' is not allowed to use these"
                f" devices as targets: {', '.join(restricted_devices)}"
            )
            self.log("info", result, logger="security")
        self.run_targets = allowed_devices
        summary = defaultdict(list)
        if self.iteration_devices and not self.iteration_run:
            if not self.workflow:
                result = "Device iteration not allowed outside of a workflow"
                return {"success": False, "result": result, "runtime": self.runtime}
            self.write_state(
                "progress/device/total", len(self.run_targets), "increment"
            )
            for device in self.run_targets:
                key = "success" if self.device_iteration(device) else "failure"
                self.write_state(f"progress/device/{key}", 1, "increment")
                summary[key].append(device.name)
            return {
                "success": not summary["failure"],
                "summary": summary,
                "runtime": self.runtime,
            }
        self.write_state(
            f"{self.progress_key}/total", len(self.run_targets), "increment"
        )
        non_skipped_targets, skipped_targets, results = [], [], []
        skip_service = self.skip.get(getattr(self.workflow, "name", None))
        if skip_service:
            self.write_state("status", "Skipped")
        if (
            self.run_method == "once"
            and not self.run_targets
            and self.eval(self.skip_query, **locals())[0]
        ):
            self.write_state("status", "Skipped")
            return {
                "success": self.skip_value == "success",
                "result": "skipped",
                "runtime": self.runtime,
            }
        for device in self.run_targets:
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
        all_skipped = self.run_targets and not non_skipped_targets
        self.run_targets = non_skipped_targets
        if self.run_method != "per_device":
            if all_skipped:
                summary[self.skip_value] = skipped_targets
                return {"success": self.skip_value == "success", "summary": summary}
            results = self.run_job_and_collect_results()
            if "summary" not in results:
                default_key = "success" if results["success"] else "failure"
                device_names = [device.name for device in self.run_targets]
                key = results.get("outgoing_edge", default_key)
                summary[key].extend(device_names)
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
            if self.is_main_run and not self.run_targets:
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
                refetch_ids = {
                    key: value.id
                    for key, value in self.kwargs.items()
                    if hasattr(value, "id")
                }
                process_args = [
                    (device.id, self.runtime, results, refetch_ids)
                    for device in non_skipped_targets
                ]
                self.log("info", f"Starting a pool of {processes} threads")
                with ThreadPool(processes=processes) as pool:
                    pool.map(self.get_device_result_in_process, process_args)
            else:
                results.extend(
                    [
                        self.run_job_and_collect_results(device, commit=False)
                        for device in non_skipped_targets
                    ]
                )
            for result in results:
                default_key = "success" if result["success"] else "failure"
                key = result.get("outgoing_edge", default_key)
                summary[key].append(result["device_target"])
            return {
                "summary": summary,
                "success": all(result["success"] for result in results if result),
                "runtime": self.runtime,
            }

    def check_size(self, data, data_type):
        column_type = "pickletype" if data_type == "result" else "large_string"
        data_size = getsizeof(str(data))
        self.write_state("memory_size", data_size, "increment", top_level=True)
        if data_type == "result":
            data["memory_size"] = data_size
        max_allowed_size = vs.database["columns"]["length"][column_type]
        allow_truncate = vs.automation["advanced"]["truncate_logs"]["active"]
        truncate_size = vs.automation["advanced"]["truncate_logs"]["maximum_size"]
        if data_type == "log" and allow_truncate and data_size > truncate_size:
            message = f"Log data is too large: truncated to {truncate_size} characters."
            self.log("warning", message)
            data = f"{data[:truncate_size]}\n{message}"
        elif data_size >= max_allowed_size:
            logs = (
                f"The {data_type} is too large to be committed to the database: "
                f"Size: {data_size}B / Maximum Allowed Size: {max_allowed_size}B"
            )
            self.log("critical", logs)
            raise Exception(f"{data_type.capitalize()} Data Overflow")
        else:
            size_percentage = data_size / max_allowed_size * 100
            log = f"The {data_type} is {size_percentage:.1f}% the maximum allowed size."
            if size_percentage > 50:
                self.log("warning", log)
        return data

    def create_transient_report(self, report):
        vs.service_report[self.parent_runtime][self.service.id] = report

    def create_transient_result(self, result, device):
        device_key = device.id if device else None
        if env.redis_queue:
            path = f"{self.parent_runtime}/results/{self.service.id}/{device_key}"
            env.redis("lpush", path, or_dumps(result, option=OPT_NON_STR_KEYS))
        else:
            vs.service_result[self.parent_runtime][self.service.id][device_key].append(
                result
            )

    def create_result(self, results, device=None, commit=True, run_result=False):
        self.success = results["success"]
        result_kw = {
            "parent_runtime": self.parent_runtime,
            "parent_service_id": self.cache["main_run_service"]["id"],
            "path": self.path,
            "run_id": self.main_run.id,
            "service_id": self.service.id,
            "labels": self.main_run.labels,
            "creator": self.main_run.creator,
        }
        if self.workflow:
            result_kw["workflow_id"] = self.workflow.id
        if self.parent_device:
            result_kw["parent_device_id"] = self.parent_device.id
        if device:
            result_kw["device_id"] = device.id
        if self.is_main_run:
            results["trigger"] = self.main_run.trigger
        if self.is_main_run and not device:
            results["payload"] = self.payload
            if self.main_run.trigger == "REST API" and not self.high_performance:
                results["devices"] = {}
                for result in self.main_run.results:
                    if not result.device:
                        continue
                    results["devices"][result.device.name] = result.result
        else:
            results.pop("payload", None)
        create_failed_results = self.disable_result_creation and not self.success
        results = self.make_json_compliant(results)
        results = self.check_size(results, "result")
        result_kw["memory_size"] = results["memory_size"]
        result_kw["result"] = results
        if not self.disable_result_creation or create_failed_results or run_result:
            self.has_result = True
            if not self.high_performance:
                try:
                    db.factory(
                        "result",
                        commit=vs.automation["advanced"]["always_commit"] or commit,
                        rbac=None,
                        **result_kw,
                    )
                except Exception:
                    self.log("critical", f"Failed to commit result:\n{format_exc()}")
                    db.session.rollback()
            else:
                for key in ("duration", "runtime", "success"):
                    result_kw[key] = results[key]
                result_kw["name"] = f"{results['runtime']} - {vs.get_persistent_id()}"
                self.create_transient_result(result_kw, device)
        return results

    def compute_devices_from_query(_self, query, property, **locals):  # noqa: N805
        values = _self.eval(query, **locals)[0]
        devices, not_found = set(), []
        if isinstance(values, str):
            values = [values]
        if all(isinstance(value, vs.models["device"]) for value in values):
            return set(values)
        elif _self.high_performance:
            with db.session_scope(remove=_self.in_process):
                devices = set(
                    db.query("device", user=_self.creator)
                    .options(selectinload(vs.models["device"].gateways))
                    .filter(getattr(vs.models["device"], property).in_(values))
                    .all()
                )
            if len(devices) != len(values):
                found = {getattr(device, property) for device in devices}
                not_found = set(values) - found
        else:
            for value in values:
                device = db.fetch(
                    "device",
                    allow_none=True,
                    user=_self.creator,
                    **{property: str(value)},
                )
                if device:
                    devices.add(device)
                else:
                    not_found.append(str(value))
        if not_found:
            raise Exception(f"Device query invalid targets: {', '.join(not_found)}")
        return devices

    def compute_run_targets(self):
        devices = set(self.get_target_property("target_devices"))
        pools = self.get_target_property("target_pools")
        if self.get_target_property("device_query"):
            devices |= self.compute_devices_from_query(
                self.get_target_property("device_query"),
                self.get_target_property("device_query_property"),
            )
        if not self.high_performance:
            if self.is_main_run:
                self.main_run.target_devices = list(devices)
                self.main_run.target_pools = list(pools)
            for pool in pools:
                if self.update_target_pools:
                    pool.compute_pool()
                devices |= set(pool.devices)
                db.session.commit()
        else:
            devices |= set().union(*(pool.devices for pool in pools))
        return devices

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

    def device_iteration(self, device):
        derived_devices = self.compute_devices_from_query(
            self.service.iteration_devices,
            self.service.iteration_devices_property,
            **locals(),
        )
        service_run = Runner(
            self.run,
            iteration_run=True,
            payload=self.payload,
            service=self.service,
            run_targets=derived_devices,
            workflow=self.workflow,
            parent_device=device,
            parent=self,
            parent_runtime=self.parent_runtime,
        )
        return service_run.start_run()["success"]

    def eval(_self, query, function="eval", **locals):  # noqa: N805
        exec_variables = _self.global_variables(**locals)
        try:
            results = builtins[function](query, exec_variables) if query else ""
        except Exception as exc:
            exc.args = (
                (
                    f"Error when executing user query:\n"
                    f"Query: '{query}'\nError: '{str(exc)}'"
                ),
            )
            raise
        return results, exec_variables

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
            self.check_size(report, "report")
            if not self.high_performance:
                db.factory(
                    "service_report",
                    runtime=self.parent_runtime,
                    service=self.service.id,
                    content=report,
                    commit=vs.automation["advanced"]["always_commit"],
                    rbac=None,
                )
            else:
                self.create_transient_report(report)
        return report

    def get(self, property):
        if self.parameterized_run and property in self.payload["form"]:
            return self.payload["form"][property]
        else:
            return getattr(self, property)

    @staticmethod
    def get_device_result_in_process(args):
        device_id, runtime, results, refetch_ids = args
        run = vs.run_instances[runtime]
        if not run.high_performance:
            device = db.fetch("device", id=device_id, rbac=None)
            run_kwargs = {"in_process": True}
            for key, value in run.kwargs.items():
                try:
                    run_kwargs[key] = db.fetch(
                        value.type, id=refetch_ids[key], rbac=None
                    )
                except Exception as exc:
                    if isinstance(exc, SQLAlchemyError):
                        db.session.rollback()
                    run_kwargs[key] = value
            if isinstance(run, vs.models["run"]):
                run = db.fetch("run", runtime=run.runtime, rbac=None)
        else:
            with db.session_scope(remove=True):
                device = (
                    db.session.query(vs.models["device"])
                    .options(selectinload(vs.models["device"].gateways))
                    .filter(vs.models["device"].id == device_id)
                    .one()
                )
            run_kwargs = {"in_process": True, **run.kwargs}
        results.append(Runner(run, **run_kwargs).run_job_and_collect_results(device))

    def get_service_properties(self):
        return {
            property: getattr(self.service, property)
            for property in ("id", "name", "scoped_name", "type")
        }

    def get_target_property(self, property):
        if (
            self.is_main_run
            and self.main_run.restart_run
            and self.payload["targets"] != "Workflow"
        ):
            if property not in ("target_devices", "target_pools"):
                return None
            if self.payload["targets"] == "Manually defined":
                model = "pool" if property == "target_pools" else "device"
                return db.fetch_all(
                    model, id_in=self.payload[f"restart_{model}s"], user=self.creator
                )
            elif self.payload["targets"] == "Restart run":
                return getattr(self.main_run.restart_run, property)
        elif self.parameterized_run and property in self.payload["form"]:
            value = self.payload["form"][property]
            if property in ("target_devices", "target_pools"):
                model = "pool" if property == "target_pools" else "device"
                value = db.fetch_all(model, id_in=value, user=self.creator)
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

    def log(
        self,
        severity,
        log,
        device=None,
        change_log=False,
        logger=None,
        service_log=True,
        allow_disable=True,
        user_defined=False,
    ):
        log_level = self.cache["main_run_service"]["log_level"]
        if (
            logger != "security"
            and allow_disable
            and (log_level == -1 or severity not in vs.log_levels[log_level:])
            and not (user_defined and self.cache["main_run_service"]["show_user_logs"])
        ):
            return
        if device:
            device_name = device if isinstance(device, str) else device.name
            log = f"DEVICE {device_name} - {log}"
        full_log = (
            f"RUNTIME {self.parent_runtime} - USER {self.creator} -"
            f" SERVICE '{self.cache['service']['name']}' - {log}"
        )
        runtime = self.parent_runtime if self.high_performance else None
        settings = env.log(
            severity,
            full_log,
            user=self.creator,
            change_log=change_log,
            logger=logger,
            runtime=runtime,
        )
        if service_log or logger and settings.get("service_log"):
            run_log = (
                f"{vs.get_time()} - {severity} - USER {self.creator} -"
                f" SERVICE {self.cache['service']['scoped_name']} - {log}"
            )
            env.log_queue(self.parent_runtime, self.cache["service"]["id"], run_log)
            if self.cache["service"]["id"] != self.cache["main_run_service"]["id"]:
                env.log_queue(
                    self.parent_runtime, self.cache["main_run_service"]["id"], run_log
                )

    def make_json_compliant(self, input):
        def rec(value):
            if isinstance(value, dict):
                return {rec(key): rec(value[key]) for key in list(value)}
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

    def notify(self, results, report):
        self.log("info", f"Sending {self.send_notification_method} notification...")
        notification = self.build_notification(results)
        file_content = deepcopy(notification)
        if self.include_device_results and not self.high_performance:
            file_content["Device Results"] = {}
            for device in self.run_targets:
                device_result = db.fetch(
                    "result",
                    service_id=self.service.id,
                    parent_runtime=self.parent_runtime,
                    device_id=device.id,
                    allow_none=True,
                    rbac=None,
                )
                if device_result:
                    file_content["Device Results"][device.name] = device_result.result
        if self.send_notification_method == "mail":
            filename = self.runtime.replace(".", "").replace(":", "")
            status = "PASS" if results["success"] else "FAILED"
            content = report if self.email_report else vs.dict_to_string(file_content)
            html_report = self.email_report and self.report_format == "html"
            result = env.send_email(
                self.sub(self.get("mail_subject"), locals())
                or f"{status}: {self.service.name}",
                content,
                recipients=self.sub(self.get("mail_recipient"), locals()),
                sender=self.sub(self.get("mail_sender"), locals()),
                reply_to=self.sub(self.get("reply_to"), locals()),
                bcc=self.sub(self.get("mail_bcc"), locals()),
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

    def run_job_and_collect_results(self, device=None, commit=True):
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

    def run_service_job(self, device):
        args = (device,) if device else ()
        retries, total_retries = self.number_of_retries + 1, 0
        results = {}
        while retries and total_retries < self.max_number_of_retries:
            if self.stop:
                self.log("error", f"ABORTING {device.name} (STOP)")
                return {"success": False, "result": "Aborted"}
            retries -= 1
            total_retries += 1
            try:
                if self.number_of_retries - retries:
                    retry = self.number_of_retries - retries
                    self.log("error", f"RETRY #{retry}", device)
                if self.service.preprocessing:
                    try:
                        self.eval(
                            self.service.preprocessing, function="exec", **locals()
                        )
                    except SystemExit:
                        pass
                try:
                    model = vs.models[self.service.type]
                    results = model.job(self.service, self, *args)
                except Exception:
                    result = "\n".join(format_exc().splitlines())
                    self.log("error", result, device)
                    results = {"success": False, "result": result}
                results = self.convert_result(results)
                if "success" not in results:
                    results["success"] = True
                if self.dry_run:
                    self.write_state("dry_run", True)
                    results["dry_run"] = True
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
                results = {"result": result, "result_dict": results, "success": False}
        return results

    def safe_log(self, original, modified):
        if "get_secret" in original or "get_credential" in original:
            return original
        else:
            return modified

    def start_run(self):
        self.init_state()
        self.write_state("status", "Running")
        start = datetime.now().replace(microsecond=0)
        results = {"runtime": self.runtime, "success": True}
        self.write_state("runtime", self.runtime)
        try:
            results.update(self.compute_targets_and_collect_results())
        except Exception:
            result = "\n".join(format_exc().splitlines())
            self.log("error", result)
            results.update({"success": False, "result": result})
        finally:
            if not self.high_performance:
                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    error = "\n".join(format_exc().splitlines())
                    self.log("error", error)
                    results.update({"success": False, "error": error})
            report = self.generate_report(results) if self.service.report else ""
            if self.get("send_notification"):
                try:
                    results = self.notify(results, report)
                except Exception:
                    error = "\n".join(format_exc().splitlines())
                    self.log("error", f"Notification error: {error}")
                    results["notification"] = {"success": False, "error": error}
            now = datetime.now().replace(microsecond=0)
            results["duration"] = str(now - start)
            self.write_state("success", results["success"])
            if self.is_main_run:
                if isinstance(self.service, SimpleNamespace):
                    properties = vars(self.service)
                    properties.update({"target_devices": None, "target_pools": None})
                else:
                    properties = self.service.get_properties(exclude=["positions"])
                results["properties"] = properties
            must_have_results = not self.has_result and not self.iteration_devices
            if self.is_main_run or len(self.run_targets) > 1 or must_have_results:
                results = self.create_result(results, run_result=self.is_main_run)
            vs.custom.run_post_processing(self, results)
        vs.run_instances.pop(self.runtime)
        return results

    @property
    def stop(self):
        if env.redis_queue:
            return bool(env.redis("get", f"stop/{self.parent_runtime}"))
        else:
            return vs.run_stop[self.parent_runtime]

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

    def validate_result(self, section, device):
        if self.validation_method == "text":
            match = self.sub(self.content_match, locals())
            str_section = str(section)
            if self.delete_spaces_before_matching:
                match, str_section = map(vs.space_deleter, (match, str_section))
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

    def write_state(self, path, value, method=None, top_level=False):
        parent_path = "" if top_level else f"/{self.path}"
        if env.redis_queue:
            if isinstance(value, bool):
                value = str(value)
            env.redis(
                {
                    None: "set",
                    "append": "lpush",
                    "increment": "incr",
                    "delete": "delete",
                }[method],
                f"{self.parent_runtime}/state{parent_path}/{path}",
                value,
            )
        else:
            *keys, last = f"{self.parent_runtime}{parent_path}/{path}".split("/")
            store = vs.run_states
            for key in keys:
                store = store.setdefault(key, {})
            if not method:
                store[last] = value
            elif method == "increment":
                store.setdefault(last, 0)
                store[last] += value
            elif method == "delete":
                store.pop(last, None)
            else:
                store.setdefault(last, []).append(value)


class NetworkManagement:
    def check_connection_numbers(self):
        if not vs.automation["connections"]["enforce_threshold"]:
            return
        total_connections = sum(
            len(vs.connections_cache[library].get(self.parent_runtime, {}))
            for library in ("netmiko", "scrapli", "napalm")
        )
        if total_connections >= vs.automation["connections"]["threshold"]:
            log = f"Too many connections open in parallel ({total_connections})"
            self.log(vs.automation["connections"]["log_level"], log)
            if vs.automation["connections"]["raise_exception"]:
                raise OverflowError(log)

    def close_device_connection(self, device):
        for library in ("netmiko", "napalm", "scrapli", "ncclient"):
            connection = self.get_connection(library, device)
            if connection:
                self.disconnect(library, device, connection)

    def configuration_transaction(self, property, device, **kwargs):
        deferred_device = (
            db.query("device", user=self.creator)
            .options(load_only(getattr(vs.models["device"], property)))
            .filter_by(id=device.id)
            .one()
        )
        previous_config = getattr(deferred_device, property)
        write_config = kwargs["success"] and previous_config != kwargs["result"]

        def transaction():
            setattr(device, f"last_{property}_runtime", str(kwargs["runtime"]))
            if kwargs["success"]:
                setattr(device, f"last_{property}_status", "Success")
                duration = f"{(datetime.now() - kwargs['runtime']).total_seconds()}s"
                setattr(device, f"last_{property}_duration", duration)
                if previous_config != kwargs["result"]:
                    setattr(deferred_device, property, kwargs["result"])
                    setattr(device, f"last_{property}_update", str(kwargs["runtime"]))
                setattr(device, f"last_{property}_success", str(kwargs["runtime"]))
            else:
                setattr(device, f"last_{property}_status", "Failure")
                setattr(device, f"last_{property}_failure", str(kwargs["runtime"]))

        db.try_commit(transaction)
        return write_config

    def disconnect(self, library, device, connection):
        connection_log = f"{library} connection '{connection.connection_name}'"
        try:
            if library == "netmiko":
                connection.disconnect()
            elif library == "ncclient":
                connection.close_session()
            else:
                connection.close()
            vs.connections_cache[library][self.parent_runtime][device].pop(
                connection.connection_name
            )
            if not vs.connections_cache[library][self.parent_runtime][device]:
                vs.connections_cache[library][self.parent_runtime].pop(device)
            self.write_state(f"connections/{library}", -1, "increment", True)
            self.log("info", f"Closed {connection_log}", device)
        except Exception:
            self.log("error", f"Error closing {connection_log}\n{format_exc()}", device)

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
            log_command = (
                "jump on connect password" if password and send == password else send
            )
            self.log("info", f"Sent '{log_command}'" f", waiting for '{expect}'")
            connection.send_command(
                send,
                expect_string=expect,
                auto_find_prompt=False,
                read_timeout=self.read_timeout,
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
            read_timeout=self.read_timeout,
            strip_prompt=False,
            strip_command=True,
        )

    def get_connection(self, library, device, name=None):
        cache = vs.connections_cache[library].get(self.parent_runtime, {})
        connection = name or getattr(self, "connection_name", "default")
        return cache.get(device, {}).get(connection)

    def get_credentials(self, device, add_secret=True):
        result, credential_type = {}, self.cache["main_run_service"]["credential_type"]
        credential = None
        if self.credentials == "object":
            if self.high_performance:
                with db.session_scope(remove=self.in_process):
                    credential = db.fetch(
                        "credential",
                        user=self.creator,
                        rbac="use",
                        id=self.named_credential_id,
                    )
            else:
                credential = self.named_credential
        elif self.credentials == "device" or add_secret:
            with db.session_scope(remove=self.high_performance and self.in_process):
                credential = db.get_credential(
                    self.creator,
                    device=device,
                    credential_type=credential_type,
                    optional=self.credentials != "device",
                )
        if credential:
            device_log = f" for '{device.name}'" if device else ""
            if self.credentials == "custom":
                device_log += " (for 'enable' / 'secret' password only, if needed)"
            self.log("info", f"Using '{credential.name}' credential{device_log}")
        if add_secret and device and credential:
            result["secret"] = env.get_password(credential.enable_password)
        if self.credentials in ("device", "object"):
            result["username"] = credential.username
            if credential.subtype == "password":
                result["password"] = env.get_password(credential.password)
            else:
                private_key = env.get_password(credential.private_key)
                result["pkey"] = RSAKey.from_private_key(StringIO(private_key))
        else:
            result["username"] = self.sub(self.custom_username, locals())
            self.log("info", f"Using Custom Credentials (user: {result['username']})")
            password = env.get_password(self.custom_password)
            substituted_password = self.sub(password, locals())
            if password != substituted_password:
                if substituted_password.startswith("b'"):
                    substituted_password = substituted_password[2:-1]
                password = env.get_password(substituted_password)
            result["password"] = password
        return result

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

    def napalm_connection(self, device):
        connection = self.get_or_close_connection("napalm", device.name)
        connection_name = f"NAPALM Connection '{self.connection_name}'"
        if connection:
            self.log("info", f"Using cached {connection_name}", device)
            return connection
        self.check_connection_numbers()
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
        napalm_connection.connection_name = self.connection_name
        self.write_state("connections/napalm", 1, "increment", True)
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
        ncclient_connection.connection_name = self.connection_name
        vs.connections_cache["ncclient"][self.parent_runtime].setdefault(
            device.name, {}
        )[self.connection_name] = ncclient_connection
        return ncclient_connection

    def netmiko_connection(self, device):
        connection = self.get_or_close_connection("netmiko", device.name)
        connection_name = f"Netmiko Connection '{self.connection_name}'"
        if connection:
            self.log("info", f"Using cached {connection_name}", device)
            return self.update_netmiko_connection(connection, device)
        self.check_connection_numbers()
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
            timeout=self.conn_timeout,
            conn_timeout=self.conn_timeout,
            auth_timeout=self.auth_timeout or None,
            banner_timeout=self.banner_timeout,
            read_timeout_override=self.read_timeout,
            fast_cli=False,
            global_delay_factor=self.global_delay_factor,
            session_log=BytesIO(),
            sock=sock,
            **vs.automation["netmiko"]["connection_args"],
            **self.get_credentials(device),
        )
        if self.enable_mode:
            netmiko_connection.enable()
        self.write_state("connections/netmiko", 1, "increment", True)
        if self.config_mode:
            kwargs = {}
            if getattr(self, "config_mode_command", None):
                kwargs["config_command"] = self.config_mode_command
            netmiko_connection.config_mode(**kwargs)
        netmiko_connection.password = "*" * 8
        netmiko_connection.secret = "*" * 8
        netmiko_connection.connection_name = self.connection_name
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
        self.check_connection_numbers()
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
        connection.connection_name = self.connection_name
        self.write_state("connections/scrapli", 1, "increment", True)
        vs.connections_cache["scrapli"][self.parent_runtime].setdefault(
            device.name, {}
        )[self.connection_name] = connection
        return connection

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

    def update_netmiko_connection(self, connection, device):
        setattr(connection, "global_delay_factor", self.service.global_delay_factor)
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
            self.log("error", f"Failed to honor the enable mode ({exc})", device)
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
            self.log("error", f"Failed to honor the config mode ({exc})", device)
        return connection


class GlobalVariables:
    @staticmethod
    def _import(module, *args, **kwargs):
        if module in vs.settings["security"]["forbidden_python_libraries"]:
            raise ImportError(f"Module '{module}' is restricted.")
        return importlib_import(module, *args, **kwargs)

    def get_all_results(self):
        return db.fetch_all("result", parent_runtime=self.parent_runtime, rbac=None)

    def get_credential(self, **kwargs):
        with db.session_scope(remove=self.high_performance and self.in_process):
            credential = db.get_credential(self.creator, **kwargs)
        credential_dict = {"username": credential.username}
        if credential.subtype == "password":
            credential_dict["password"] = env.get_password(credential.password)
        else:
            private_key = env.get_password(credential.private_key)
            credential_dict["pkey"] = RSAKey.from_private_key(StringIO(private_key))
        credential_dict["secret"] = env.get_password(credential.enable_password)
        return credential_dict

    def get_data(self, path=None, persistent_id=None):
        kwargs = {"path": path} if path else {"persistent_id": persistent_id}
        with db.session_scope(remove=self.high_performance and self.in_process):
            data = db.fetch("data", user=self.creator, rbac="use", **kwargs)
            return SimpleNamespace(**data.get_properties())

    def get_result(
        self, service_name, device=None, workflow=None, runtime=None, all_matches=False
    ):
        def filter_run(query, property):
            query = query.filter(
                vs.models["result"].service.has(
                    getattr(vs.models["service"], property) == service_name
                )
            )
            return query.all()

        def get_transient_results():
            scoped_name_cache = self.cache["topology"]["scoped_name_to_dict"]
            service_cache = self.cache["topology"]["name_to_dict"]["services"]
            device_cache = self.cache["topology"]["name_to_dict"]["devices"]
            if service_ns := scoped_name_cache.get(service_name):
                service_key = service_ns.id
            elif service_ns := service_cache.get(service_name):
                service_key = service_ns.id
            else:
                return
            device_key = None
            if device:
                if device not in device_cache:
                    return
                device_key = device_cache[device].id
            device_key = device_cache[device].id if device in device_cache else "*"
            if env.redis_queue:
                path = f"{self.parent_runtime}/results/{service_key}/{device_key}"
                if device:
                    results = list(map(or_loads, env.redis("lrange", path, 0, -1)))
                else:
                    results = [
                        or_loads(result)
                        for key in env.redis("keys", path)
                        for result in env.redis("lrange", key, 0, -1)
                    ]
            else:
                results_store = vs.service_result.get(runtime or self.parent_runtime)
                if not env.redis_queue and not results_store:
                    return
                results_store = results_store.get(service_key)
                if not results_store:
                    return
                if device:
                    results = results_store.get(device_key, [])
                else:
                    results = sum(results_store.values(), [])
            if all_matches:
                return [result["result"] for result in results]
            else:
                return results[0]["result"] if results else None

        def recursive_search(run):
            if not run:
                return None
            if self.high_performance and run == self.main_run:
                if results := get_transient_results():
                    return results
            with db.session_scope(remove=self.high_performance and self.in_process):
                query = db.session.query(vs.models["result"]).filter(
                    vs.models["result"].parent_runtime == (runtime or run.runtime)
                )
                if workflow:
                    query = query.filter(
                        vs.models["result"].workflow.has(
                            vs.models["workflow"].name == workflow
                        )
                    )
                if device:
                    query = query.filter(
                        vs.models["result"].device.has(
                            vs.models["device"].name == device
                        )
                    )
                results = filter_run(query, "scoped_name") or filter_run(query, "name")
                results = [result.result for result in results]
            if not results:
                return recursive_search(run.restart_run)
            else:
                return results if all_matches else results[0]

        return recursive_search(self.main_run)

    def get_secret(self, name):
        with db.session_scope(remove=self.high_performance and self.in_process):
            secret = db.fetch("secret", scoped_name=name, user=self.creator, rbac="use")
            return env.get_password(secret.secret_value)

    def get_var(self, *args, **kwargs):
        return self.payload_helper(*args, operation="get", **kwargs)

    def global_variables(_self, **locals):  # noqa: N805
        payload, device = _self.payload, locals.get("device")
        variables = {**locals, **payload.get("form", {})}
        variables.update(payload.get("variables", {}))
        if device and "devices" in payload.get("variables", {}):
            variables.update(payload["variables"]["devices"].get(device.name, {}))
        variables.update(
            {
                "__builtins__": {**builtins, "__import__": _self._import},
                "delete": partial(_self.internal_function, "delete"),
                "devices": _self.run_targets,
                "dry_run": getattr(_self, "dry_run", False),
                "get_all_results": _self.get_all_results,
                "get_connection": _self.get_connection,
                "get_var": _self.get_var,
                "factory": partial(_self.internal_function, "factory"),
                "fetch": partial(_self.internal_function, "fetch"),
                "fetch_all": partial(_self.internal_function, "fetch_all"),
                "filtering": partial(_self.internal_function, "filtering"),
                "get_result": _self.get_result,
                "get_secret": _self.get_secret,
                "get_data": _self.get_data,
                "log": partial(_self.log, user_defined=True),
                "parent_device": _self.parent_device or device,
                "payload": _self.payload,
                "remove_note": _self.remove_note,
                "set_note": _self.set_note,
                "set_var": _self.payload_helper,
                "workflow": _self.workflow,
                **_self.cache["global_variables"],
                **vs.custom.runner_global_variables(_self),
            }
        )
        if _self.cache["creator"]["is_admin"]:
            variables["get_credential"] = _self.get_credential
            variables["redis"] = env.redis
        return variables

    def internal_function(self, func, _model, **kwargs):
        if _model not in vs.automation["workflow"]["allowed_models"][func]:
            raise db.rbac_error(f"Use of '{func}' not allowed on {_model}s.")
        kwargs.update({"rbac": "edit", "user": self.creator})
        if func == "filtering":
            kwargs["bulk"] = "object"
        target = controller if func == "filtering" else db
        if self.high_performance:
            with db.session_scope(commit=func == "factory", remove=self.in_process):
                result = getattr(target, func)(_model, **kwargs)
                if func == "delete" or not result:
                    return result
                elif isinstance(result, list):
                    return [
                        SimpleNamespace(**instance.get_properties())
                        for instance in result
                    ]
                else:
                    return SimpleNamespace(**result.get_properties())
        else:
            return getattr(target, func)(_model, **kwargs)

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

    def remove_note(self, x, y):
        self.write_state(f"notes/{x}_{y}", "", top_level=True, method="delete")

    def set_note(self, x, y, content):
        self.write_state(f"notes/{x}_{y}", content, top_level=True)


class Runner(GlobalVariables, NetworkManagement, RunEngine, vs.TimingMixin):
    pass
