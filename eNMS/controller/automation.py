from apscheduler.jobstores.base import JobLookupError
from collections import defaultdict
from datetime import datetime
from flask import request, session
from flask_login import current_user
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko.ssh_dispatcher import CLASS_MAPPER, FILE_TRANSFER_MAP
from pathlib import Path
from re import search, sub
from uuid import uuid4

from eNMS.controller.base import BaseController
from eNMS.database import Session
from eNMS.database.functions import delete, factory, fetch, fetch_all


class AutomationController(BaseController):

    NETMIKO_DRIVERS = sorted((driver, driver) for driver in CLASS_MAPPER)
    NETMIKO_SCP_DRIVERS = sorted((driver, driver) for driver in FILE_TRANSFER_MAP)
    NAPALM_DRIVERS = sorted((driver, driver) for driver in SUPPORTED_DRIVERS[1:])
    connections_cache = {"napalm": defaultdict(dict), "netmiko": defaultdict(dict)}
    service_db = defaultdict(lambda: {"runs": 0})
    run_db = defaultdict(dict)
    run_logs = defaultdict(list)

    def stop_workflow(self, runtime):
        run = fetch("run", allow_none=True, runtime=runtime)
        if run and run.run_state["status"] == "Running":
            run.run_state["status"] = "stop"
            return True

    def add_edge(self, workflow_id, subtype, source, destination):
        workflow_edge = factory(
            "workflow_edge",
            **{
                "name": f"{workflow_id}-{subtype}:{source}->{destination}",
                "workflow": workflow_id,
                "subtype": subtype,
                "source": source,
                "destination": destination,
            },
        )
        Session.commit()
        now = self.get_time()
        fetch("workflow", id=workflow_id).last_modified = now
        return {"edge": workflow_edge.serialized, "update_time": now}

    def add_service_to_workflow(self, workflow, service):
        workflow = fetch("workflow", id=workflow)
        workflow.services.append(fetch("service", id=service))

    def copy_service_in_workflow(self, workflow_id, **kwargs):
        print(kwargs)
        service = fetch("service", id=kwargs["services"])
        workflow = fetch("workflow", id=workflow_id)
        if kwargs["mode"] == "deep":
            service = service.duplicate(workflow)
        elif not service.shared:
            return {"error": "This is not a shared service."}
        elif service in workflow.services:
            return {"error": f"This workflow already contains {service.name}."}
        else:
            workflow.services.append(service)
        workflow.last_modified = self.get_time()
        Session.commit()
        return {"service": service.serialized, "update_time": workflow.last_modified}

    def clear_results(self, service_id):
        for result in fetch(
            "run", all_matches=True, allow_none=True, service_id=service_id
        ):
            Session.delete(result)

    def create_label(self, workflow_id, x, y, **kwargs):
        workflow, label_id = fetch("workflow", id=workflow_id), str(uuid4())
        label = {
            "positions": [x, y],
            "content": kwargs["text"],
            "alignment": kwargs["alignment"],
        }
        workflow.labels[label_id] = label
        return {"id": label_id, **label}

    def delete_edge(self, workflow_id, edge_id):
        delete("workflow_edge", id=edge_id)
        now = self.get_time()
        fetch("workflow", id=workflow_id).last_modified = now
        return now

    def delete_node(self, workflow_id, service_id):
        workflow, service = (
            fetch("workflow", id=workflow_id),
            fetch("service", id=service_id),
        )
        workflow.services.remove(service)
        if not service.shared:
            Session.delete(service)
        now = self.get_time()
        workflow.last_modified = now
        return {"service": service.serialized, "update_time": now}

    def delete_label(self, workflow_id, label):
        workflow = fetch("workflow", id=workflow_id)
        workflow.labels.pop(label)
        now = self.get_time()
        workflow.last_modified = now
        return now

    def duplicate_workflow(self, workflow_id, **kwargs):
        return fetch("workflow", id=workflow_id).duplicate(**kwargs).serialized

    def get_service_logs(self, runtime):
        run = fetch("run", allow_none=True, runtime=runtime)
        result = run.result() if run else None
        logs = result["logs"] if result else self.run_logs.get(runtime, [])
        return {"logs": "\n".join(logs), "refresh": not bool(result)}

    def get_runtimes(self, type, id):
        runs = fetch("run", allow_none=True, all_matches=True, service_id=id)
        return sorted(set((run.parent_runtime, run.name) for run in runs))

    def get_result(self, id):
        return fetch("result", id=id).result

    def get_workflow_services(self, workflow):
        if not workflow:
            return [
                {
                    "id": workflow.id,
                    "text": workflow.name,
                    "children": True,
                    "type": "workflow",
                }
                for workflow in fetch_all("workflow")
                if not workflow.workflows
            ]
        else:
            return [
                {
                    "id": service.id,
                    "text": service.scoped_name,
                    "children": service.type == "workflow",
                    "type": "workflow" if service.type == "workflow" else "service",
                }
                for service in fetch("workflow", id=workflow).services
                if service.scoped_name not in ("Start", "End")
            ]

    @staticmethod
    def run(service, **kwargs):
        run_kwargs = {
            key: kwargs.pop(key)
            for key in ("creator", "runtime", "task", "devices", "pools")
            if kwargs.get(key)
        }
        restart_run = fetch(
            "run",
            allow_none=True,
            service_id=service,
            runtime=kwargs.get("restart_runtime"),
        )
        if restart_run:
            run_kwargs["restart_run"] = restart_run
        run = factory("run", service=service, **run_kwargs)
        run.properties = kwargs
        return run.run(kwargs.get("payload"))

    def run_service(self, id=None, **kwargs):
        for property in ("user", "csrf_token", "form_type"):
            kwargs.pop(property, None)
        kwargs["creator"] = getattr(current_user, "name", "admin")
        service = fetch("service", id=id)
        kwargs["runtime"] = runtime = self.get_time()
        if kwargs.get("asynchronous", True):
            self.scheduler.add_job(
                id=self.get_time(),
                func=self.run,
                run_date=datetime.now(),
                args=[id],
                kwargs=kwargs,
                trigger="date",
            )
        else:
            service.run(runtime=runtime)
        return {"service": service.serialized, "runtime": runtime}

    def save_positions(self, workflow_id):
        now = self.get_time()
        workflow = fetch("workflow", allow_none=True, id=workflow_id)
        session["workflow"] = workflow.id
        for id, position in request.json.items():
            new_position = [position["x"], position["y"]]
            if "-" in id:
                old_position = workflow.labels[id].pop("positions")
                workflow.labels[id] = {"positions": new_position, **workflow.labels[id]}
            else:
                service = fetch("service", id=id)
                old_position = service.positions.get(workflow.name)
                service.positions[workflow.name] = new_position
            if new_position != old_position:
                workflow.last_modified = now
        return now

    def skip_services(self, workflow_id, service_ids):
        services = [fetch("service", id=id) for id in service_ids.split("-")]
        skip = not all(service.skip for service in services)
        for service in services:
            service.skip = skip
        fetch("workflow", id=workflow_id).last_modified = self.get_time()
        return "skip" if skip else "unskip"

    def get_service_state(self, service_id, runtime="latest"):
        state, service = None, fetch("service", id=service_id)
        runs = fetch_all("run", service_id=service_id)
        if runs and runtime != "normal":
            if runtime == "latest":
                runtime = runs[-1].parent_runtime
            state = self.run_db.get(runtime) or fetch("run", runtime=runtime).state
        return {
            "service": service.to_dict(include=["services", "edges"]),
            "runtimes": [(r.parent_runtime, r.creator) for r in runs],
            "state": state,
            "runtime": runtime,
        }

    def convert_date(self, date):
        python_month = search(r".*-(\d{2})-.*", date).group(1)
        month = "{:02}".format((int(python_month) - 1) % 12)
        return [
            int(i)
            for i in sub(
                r"(\d+)-(\d+)-(\d+) (\d+):(\d+).*", r"\1," + month + r",\3,\4,\5", date
            ).split(",")
        ]

    def calendar_init(self, type):
        results = {}
        for instance in fetch_all(type):
            if getattr(instance, "workflow", None):
                continue
            date = getattr(instance, "next_run_time" if type == "task" else "runtime")
            if date:
                results[instance.name] = {
                    "start": self.convert_date(date),
                    **instance.serialized,
                }
        return results

    def scheduler_action(self, action):
        getattr(self.scheduler, action)()

    def task_action(self, action, task_id):
        try:
            return getattr(fetch("task", id=task_id), action)()
        except JobLookupError:
            return {"error": "This task no longer exists."}

    def scan_playbook_folder(self):
        path = Path(
            self.config["paths"]["playbooks"] or self.path / "files" / "playbooks"
        )
        playbooks = [[str(f) for f in path.glob(e)] for e in ("*.yaml", "*.yml")]
        return sorted(sum(playbooks, []))
