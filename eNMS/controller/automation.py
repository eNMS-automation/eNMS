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
