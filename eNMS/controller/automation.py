from collections import defaultdict
from flask_login import current_user
from operator import attrgetter, itemgetter
from pathlib import Path
from re import search, sub
from threading import Thread
from uuid import uuid4

from eNMS import app
from eNMS.database import db
from eNMS.models import models


class AutomationController:
    def add_edge(self, workflow_id, subtype, source, destination):
        now = app.get_time()
        workflow = db.fetch("workflow", id=workflow_id, rbac="edit")
        workflow_edge = self.update(
            "workflow_edge",
            rbac=None,
            **{
                "name": now,
                "workflow": workflow_id,
                "subtype": subtype,
                "source": source,
                "destination": destination,
            },
        )
        db.session.commit()
        workflow.last_modified = now
        return {"edge": workflow_edge, "update_time": now}

    def calendar_init(self, type):
        results = {}
        for instance in db.fetch_all(type):
            if getattr(instance, "workflow", None):
                continue
            date = getattr(instance, "next_run_time" if type == "task" else "runtime")
            python_month = search(r".*-(\d{2})-.*", date)
            if not python_month:
                continue
            month = "{:02}".format((int(python_month.group(1)) - 1) % 12)
            start = [
                int(i)
                for i in sub(
                    r"(\d+)-(\d+)-(\d+) (\d+):(\d+).*",
                    r"\1," + month + r",\3,\4,\5",
                    date,
                ).split(",")
            ]
            results[instance.name] = {"start": start, **instance.serialized}
        return results

    def clear_results(self, service_id):
        for result in db.fetch(
            "run", all_matches=True, allow_none=True, service_id=service_id
        ):
            db.session.delete(result)

    def copy_service_in_workflow(self, workflow_id, **kwargs):
        service_sets = list(set(kwargs["services"].split(",")))
        service_instances = db.objectify("service", service_sets)
        workflow = db.fetch("workflow", id=workflow_id)
        services, errors = [], []
        if kwargs["mode"] == "shallow":
            for service in service_instances:
                if not service.shared:
                    errors.append(f"'{service.name}' is not a shared service.")
                elif service in workflow.services:
                    errors.append(f"This workflow already contains '{service.name}'.")
        if errors:
            return {"alert": errors}
        for service in service_instances:
            if kwargs["mode"] == "deep":
                service = service.duplicate(workflow)
            else:
                workflow.services.append(service)
            services.append(service)
        workflow.last_modified = app.get_time()
        db.session.commit()
        return {
            "services": [service.serialized for service in services],
            "update_time": workflow.last_modified,
        }

    def create_label(self, workflow_id, x, y, label_id, **kwargs):
        workflow = db.fetch("workflow", id=workflow_id, rbac="edit")
        label_id = str(uuid4()) if label_id == "undefined" else label_id
        label = {
            "positions": [x, y],
            "content": kwargs["text"],
            "alignment": kwargs["alignment"],
        }
        workflow.labels[label_id] = label
        return {"id": label_id, **label}

    def delete_corrupted_edges(self):
        edges = set(db.fetch_all("workflow_edge"))
        duplicated_edges, number_of_corrupted_edges = defaultdict(list), 0
        for edge in list(edges):
            services = getattr(edge.workflow, "services", [])
            if (
                not edge.source
                or not edge.destination
                or not edge.workflow
                or edge.source not in services
                or edge.destination not in services
            ):
                edges.remove(edge)
                db.session.delete(edge)
                number_of_corrupted_edges += 1
        db.session.commit()
        for edge in edges:
            duplicated_edges[
                (
                    edge.source.name,
                    edge.destination.name,
                    edge.workflow.name,
                    edge.subtype,
                )
            ].append(edge)
        for duplicates in duplicated_edges.values():
            for duplicate in duplicates[1:]:
                db.session.delete(duplicate)
                number_of_corrupted_edges += 1
        return number_of_corrupted_edges

    def delete_workflow_selection(self, workflow_id, **selection):
        workflow = db.fetch("workflow", id=workflow_id)
        workflow.last_modified = app.get_time()
        for edge_id in selection["edges"]:
            db.delete("workflow_edge", id=edge_id)
        for node_id in selection["nodes"]:
            if isinstance(node_id, str):
                workflow.labels.pop(node_id)
            else:
                service = db.fetch("service", id=node_id)
                workflow.services.remove(service)
                if not service.shared:
                    db.delete("service", id=service.id)
        return workflow.last_modified

    def duplicate_workflow(self, workflow_id):
        workflow = db.fetch("workflow", id=workflow_id)
        return workflow.duplicate().serialized

    def get_parent_workflows(self, workflow=None):
        yield workflow
        for parent_workflow in workflow.workflows:
            yield from self.get_parent_workflows(parent_workflow)

    def get_result(self, id):
        return db.fetch("result", id=id).result

    def get_runtimes(self, type, id):
        results = db.fetch("result", allow_none=True, all_matches=True, service_id=id)
        return sorted(set((result.parent_runtime,) * 2 for result in results))

    def get_service_logs(self, service, runtime, start_line):
        log_instance = db.fetch(
            "service_log", allow_none=True, runtime=runtime, service_id=service
        )
        number_of_lines = 0
        if log_instance:
            logs = log_instance.content
        else:
            lines = (
                app.log_queue(runtime, service, start_line=int(start_line), mode="get")
                or []
            )
            number_of_lines, logs = len(lines), "\n".join(lines)
        return {
            "logs": logs,
            "refresh": not log_instance,
            "line": int(start_line) + number_of_lines,
        }

    def get_service_state(self, path, runtime=None):
        service_id, state = path.split(">")[-1], None
        service = db.fetch("service", id=service_id, allow_none=True)
        if not service:
            raise db.rbac_error
        runs = db.query("run").filter(models["run"].services.any(id=service_id)).all()
        if runtime != "normal" and runs:
            if runtime == "latest":
                run = sorted(runs, key=attrgetter("runtime"), reverse=True)[0]
            else:
                run = db.fetch("run", parent_runtime=runtime)
            state = run.get_state()
        return {
            "service": service.to_dict(include=["services", "edges", "superworkflow"]),
            "runtimes": sorted(set((r.parent_runtime, r.creator) for r in runs)),
            "state": state,
            "runtime": runtime,
        }

    def get_top_level_workflows(self):
        return [
            workflow.base_properties
            for workflow in db.fetch_all("workflow")
            if not workflow.workflows
        ]

    def get_workflow_results(self, workflow, runtime):
        run = db.fetch("run", parent_runtime=runtime)
        state = run.state

        def rec(service, path=str(run.service_id)):
            results = db.fetch(
                "result",
                parent_runtime=runtime,
                allow_none=True,
                all_matches=True,
                service_id=service.id,
            )
            if service.scoped_name in ("Start", "End") or not results:
                return
            progress = state.get(path, {}).get("progress")
            track_progress = progress and progress["device"]["total"]
            data = {"progress": progress["device"]} if track_progress else {}
            color = "32CD32" if all(result.success for result in results) else "FF6666"
            result = {
                "runtime": min(result.runtime for result in results),
                "data": {"properties": service.base_properties, **data},
                "text": service.scoped_name,
                "a_attr": {"style": f"color: #{color};width: 100%"},
            }
            if service.type == "workflow":
                children_results = []
                for child in service.services:
                    if child.scoped_name == "Placeholder":
                        child = run.placeholder
                    child_results = rec(child, f"{path}>{child.id}")
                    if not child_results:
                        continue
                    children_results.append(child_results)
                return {
                    "children": sorted(children_results, key=itemgetter("runtime")),
                    **result,
                }
            else:
                return result

        return rec(run.service)

    def get_workflow_tree(self, full_path):
        path_id = full_path.split(">")

        def rec(service, path=""):
            path += ">" * bool(path) + str(service.id)
            if service.scoped_name in ("Start", "End"):
                return
            elif service.scoped_name == "Placeholder" and len(path_id) > 1:
                service = db.fetch("workflow", id=path_id[1])
            return {
                "data": {"path": path, **service.base_properties},
                "id": service.id,
                "state": {"opened": full_path.startswith(path)},
                "text": service.scoped_name,
                "children": sorted(
                    filter(None, [rec(child, path) for child in service.services]),
                    key=lambda node: node["text"].lower(),
                )
                if service.type == "workflow"
                else False,
                "a_attr": {
                    "class": "no_checkbox",
                    "style": (
                        f"color: #{'FF1694' if service.shared else '6666FF'};"
                        "width: 100%"
                    ),
                },
                "type": service.type,
            }

        return rec(db.fetch("workflow", id=path_id[0]))

    def get_workflow_services(self, id, node):
        parents = list(self.get_parent_workflows(db.fetch("workflow", id=id)))
        if node == "all":
            return (
                [
                    {
                        "data": {"id": "standalone"},
                        "id": "standalone",
                        "text": "Standalone services",
                        "children": True,
                        "state": {"disabled": True},
                        "a_attr": {
                            "class": "no_checkbox",
                            "style": "color: #000000; width: 100%",
                        },
                        "type": "category",
                    }
                ]
                + [
                    {
                        "data": {"id": "shared"},
                        "id": "shared",
                        "text": "Shared services",
                        "children": True,
                        "state": {"disabled": True},
                        "a_attr": {
                            "class": "no_checkbox",
                            "style": "color: #FF1694; width: 100%",
                        },
                        "type": "category",
                    }
                ]
                + sorted(
                    (
                        {
                            "id": workflow.name,
                            "data": {"id": workflow.id},
                            "text": workflow.name,
                            "children": True,
                            "type": "workflow",
                            "state": {"disabled": workflow in parents},
                            "a_attr": {
                                "class": "no_checkbox" if workflow in parents else "",
                                "style": "color: #6666FF; width: 100%",
                            },
                        }
                        for workflow in db.fetch_all("workflow")
                        if not workflow.workflows
                    ),
                    key=itemgetter("text"),
                )
            )
        elif node == "standalone":
            return sorted(
                (
                    {
                        "data": {"id": service.id},
                        "text": service.scoped_name,
                        "a_attr": {"style": ("color: #6666FF;" "width: 100%")},
                    }
                    for service in db.fetch_all("service")
                    if not service.workflows and service.type != "workflow"
                ),
                key=itemgetter("text"),
            )
        elif node == "shared":
            return sorted(
                (
                    {
                        "data": {"id": service.id},
                        "text": service.scoped_name,
                        "a_attr": {"style": ("color: #FF1694;" "width: 100%")},
                    }
                    for service in db.fetch_all("service")
                    if service.shared and service.scoped_name not in ("Start", "End")
                ),
                key=itemgetter("text"),
            )
        else:
            return sorted(
                (
                    {
                        "data": {"id": service.id},
                        "text": service.scoped_name,
                        "children": service.type == "workflow",
                        "type": "workflow" if service.type == "workflow" else "service",
                        "state": {"disabled": service in parents},
                        "a_attr": {
                            "class": "no_checkbox" if service in parents else "",
                            "style": (
                                f"color: #{'FF1694' if service.shared else '6666FF'};"
                                "width: 100%"
                            ),
                        },
                    }
                    for service in db.fetch("workflow", id=node).services
                    if service.scoped_name not in ("Start", "End")
                ),
                key=itemgetter("text"),
            )

    @staticmethod
    def run(service, **kwargs):
        run_kwargs = {
            key: kwargs.pop(key)
            for key in (
                "trigger",
                "creator",
                "start_services",
                "runtime",
                "task",
                "target_devices",
                "target_pools",
            )
            if kwargs.get(key)
        }
        restart_run = db.fetch(
            "run",
            allow_none=True,
            runtime=kwargs.get("restart_runtime"),
        )
        if restart_run:
            run_kwargs["restart_run"] = restart_run
        service = db.fetch("service", id=service)
        service.status = "Running"
        initial_payload = kwargs.get("initial_payload", service.initial_payload)
        if service.type == "workflow" and service.superworkflow:
            run_kwargs["placeholder"] = run_kwargs["start_service"] = service.id
            service = service.superworkflow
            initial_payload.update(service.initial_payload)
        else:
            run_kwargs["start_service"] = service.id
        run = db.factory("run", service=service.id, commit=True, **run_kwargs)
        run.properties = kwargs
        return run.run({**initial_payload, **kwargs})

    def run_service(self, path, **kwargs):
        if isinstance(kwargs.get("start_services"), str):
            kwargs["start_services"] = kwargs["start_services"].split("-")
        service_id = str(path).split(">")[-1]
        for property in ("user", "csrf_token", "form_type"):
            kwargs.pop(property, None)
        kwargs["creator"] = getattr(current_user, "name", "")
        service = db.fetch("service", id=service_id, rbac="run")
        kwargs["runtime"] = runtime = app.get_time()
        if kwargs.get("asynchronous", True):
            Thread(target=self.run, args=(service_id,), kwargs=kwargs).start()
        else:
            service.run(runtime=runtime)
        return {
            "service": service.serialized,
            "runtime": runtime,
            "user": current_user.name,
        }

    def run_service_on_targets(self, **kwargs):
        return self.run_service(
            kwargs["service"],
            **{f"target_{kwargs['type']}s": kwargs["targets"].split("-")},
        )

    def save_positions(self, workflow_id, **kwargs):
        now, old_position = app.get_time(), None
        workflow = db.fetch("workflow", allow_none=True, id=workflow_id, rbac="edit")
        if not workflow:
            return
        for id, position in kwargs.items():
            new_position = [position["x"], position["y"]]
            if "-" not in id:
                service = db.fetch("service", id=id, rbac=None)
                old_position = service.positions.get(workflow.name)
                service.positions[workflow.name] = new_position
            elif id in workflow.labels:
                old_position = workflow.labels[id].pop("positions")
                workflow.labels[id] = {"positions": new_position, **workflow.labels[id]}
            if new_position != old_position:
                workflow.last_modified = now
        return now

    def scan_playbook_folder(self):
        path = Path(
            app.settings["paths"]["playbooks"] or app.path / "files" / "playbooks"
        )
        playbooks = [[str(f) for f in path.glob(e)] for e in ("*.yaml", "*.yml")]
        return sorted(sum(playbooks, []))

    def task_action(self, mode, task_id):
        return db.fetch("task", id=task_id, rbac="schedule").schedule(mode)

    def scheduler_action(self, mode, **kwargs):
        for task_id in self.filtering("task", bulk="id", form=kwargs):
            self.task_action(mode, task_id)

    def search_workflow_services(self, *args, **kwargs):
        return [
            "standalone",
            "shared",
            *[
                workflow.name
                for workflow in db.fetch_all("workflow")
                if any(
                    kwargs["str"].lower() in service.scoped_name.lower()
                    for service in workflow.services
                )
            ],
        ]

    def skip_services(self, workflow_id, service_ids):
        services = [db.fetch("service", id=id) for id in service_ids.split("-")]
        workflow = db.fetch("workflow", id=workflow_id)
        skip = not all(service.skip.get(workflow.name) for service in services)
        for service in services:
            service.skip[workflow.name] = skip
        workflow.last_modified = app.get_time()
        return {
            "skip": "skip" if skip else "unskip",
            "update_time": workflow.last_modified,
        }

    def stop_workflow(self, runtime):
        run = db.fetch("run", allow_none=True, runtime=runtime)
        if run and run.status == "Running":
            if app.redis_queue:
                app.redis("set", f"stop/{run.parent_runtime}", "true")
            else:
                app.run_stop[run.parent_runtime] = True
            return True
