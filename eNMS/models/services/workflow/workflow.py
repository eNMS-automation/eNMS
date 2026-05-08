from collections import defaultdict
from heapq import heappop, heappush
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import backref, deferred, relationship
from sqlalchemy.schema import UniqueConstraint

from eNMS.database import db
from eNMS.fields import (
    BooleanField,
    HiddenField,
    InstanceField,
    IntegerField,
    SelectField,
)
from eNMS.forms import ServiceForm
from eNMS.models.automation import Service
from eNMS.models.base import AbstractBase
from eNMS.runner import Runner
from eNMS.variables import vs


class Workflow(Service):
    __tablename__ = "workflow"
    pretty_name = "Workflow"
    parent_type = "service"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    category = db.Column(db.SmallString)
    close_connection = db.Column(Boolean, default=False)
    labels = db.Column(db.Dict, info={"log_change": False})
    positions = deferred(db.Column(db.Dict, default={}, info={"log_change": False}))
    services = relationship(
        "Service",
        secondary=db.service_workflow_table,
        back_populates="workflows",
    )
    edges = relationship(
        "WorkflowEdge",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )
    superworkflow_id = db.Column(
        Integer, ForeignKey("workflow.id", ondelete="SET NULL")
    )
    superworkflow = relationship(
        "Workflow", remote_side=[id], foreign_keys="Workflow.superworkflow_id"
    )
    service_changelogs = relationship(
        "Changelog",
        secondary=db.changelog_workflow_table,
        back_populates="workflows",
        info={"log_change": False},
    )

    __mapper_args__ = {"polymorphic_identity": "workflow"}

    def __init__(self, **kwargs):
        migration_import = kwargs.get("migration_import", False)
        if not migration_import:
            start = db.fetch("service", scoped_name="Start", rbac=None)
            end = db.fetch("service", scoped_name="End", rbac=None)
            self.services.extend([start, end])
            self.positions = {}
        super().__init__(**kwargs)
        if not migration_import and "[Shared] End" not in self.positions:
            self.positions["[Shared] End"] = [500, 0]

    def recursive_update(self):
        def rec(service):
            service.post_update()
            if service.type == "workflow":
                for subservice in service.services:
                    rec(subservice)

        rec(self)

    def delete(self):
        for service in self.services:
            if not service.shared:
                db.delete_instance(service)
        super().delete()

    def set_name(self, name=None):
        old_name = self.name
        super().set_name(name)
        for service in self.services:
            old_service_name = service.name
            if not service.shared:
                service.set_name()
            if old_service_name in self.positions:
                self.positions[service.name] = self.positions[old_service_name]
        for edge in self.edges:
            edge.name.replace(old_name, self.name)

    def duplicate(self, workflow=None, clone=None):
        db.session.connection().info["ignore"] = True
        if not clone:
            clone = super().duplicate(workflow)
        clone.labels = self.labels
        clone_services = {}
        db.session.commit()
        db.session.connection().info["ignore"] = True
        for service in self.exclude_soft_deleted("services"):
            if service.shared:
                service_clone = service
                if service not in clone.services:
                    clone.services.append(service)
            else:
                service_clone = service.duplicate(clone)
            clone.positions[service_clone.name] = self.positions.get(
                service.name, [0, 0]
            )
            service_clone.skip[clone.name] = service.skip.get(self.name, False)
            clone_services[service.id] = service_clone
        db.session.commit()
        db.session.connection().info["ignore"] = True
        for edge in self.exclude_soft_deleted("edges"):
            clone.edges.append(
                db.factory(
                    "workflow_edge",
                    rbac=None,
                    **{
                        "workflow": clone,
                        "color": edge.color,
                        "label": edge.label,
                        "subtype": edge.subtype,
                        "source": clone_services[edge.source.id],
                        "destination": clone_services[edge.destination.id],
                    },
                )
            )
        db.session.commit()
        if not workflow:
            clone.recursive_update()
        return clone

    @property
    def deep_services(self):
        services = [
            service.deep_services if service.type == "workflow" else [service]
            for service in self.exclude_soft_deleted("services")
        ]
        return [self] + sum(services, [])

    @property
    def deep_edges(self):
        edges = [
            list(workflow.exclude_soft_deleted("edges"))
            for workflow in set(self.deep_services)
            if workflow.type == "workflow"
        ]
        return sum(edges, [])

    @staticmethod
    def job(self, run, device=None):
        number_of_runs = defaultdict(int)
        topology = run.cache["topology"]
        start = topology["name_to_dict"]["services"]["[Shared] Start"]
        end = topology["name_to_dict"]["services"]["[Shared] End"]
        services, targets = [], defaultdict(set)
        start_targets = [device] if device else run.run_targets
        for service_id in run.start_services or [start.id]:
            service = topology["services"][int(service_id)]
            targets[service.name] |= {device.name for device in start_targets}
            heappush(services, (1 / service.priority, service.id))
        visited = set()
        tracking_bfs = run.run_method == "per_service_with_workflow_targets"
        SxS = not (tracking_bfs or device)
        device_store = {device.name: device for device in start_targets}
        while services:
            if run.stop:
                return {"success": False, "result": "Aborted"}
            _, service_id = heappop(services)
            service = topology["services"][service_id]
            if number_of_runs[service.name] >= service.maximum_runs:
                continue
            number_of_runs[service.name] += 1
            visited.add(service_id)
            if service in (start, end) or service.skip.get(self.name, False):
                success = service.skip_value == "success"
                results = {"result": "skipped", "success": success}
                if not SxS:
                    results["summary"] = defaultdict(
                        list, success=targets[service.name]
                    )
            else:
                service_kw = service
                if not run.high_performance:
                    service_kw = db.fetch("service", id=service_id, rbac=None)
                kwargs = {
                    "service": service_kw,
                    "workflow": self,
                    "parent": run,
                    "parent_runtime": run.parent_runtime,
                    "workflow_run_method": run.run_method,
                }
                if not SxS:
                    kwargs["run_targets"] = []
                    for name in targets[service.name]:
                        if name not in device_store:
                            device_store[name] = db.fetch("device", name=name)
                        kwargs["run_targets"].append(device_store[name])
                if run.parent_device:
                    kwargs["parent_device"] = run.parent_device
                service_run = Runner(run, payload=run.payload, **kwargs)
                results = service_run.start_run()
                if not results:
                    continue
            status = "success" if results["success"] else "failure"
            next_edge = results.get("outgoing_edge", status)
            summary = results.get("summary", {})
            if not tracking_bfs and not device:
                run.write_state(f"progress/service/{next_edge}", 1, "increment")
            for edge_id, successor_id in topology["neighbors"][(self.id, service_id)]:
                edge = topology["edges"][edge_id]
                successor = topology["services"][successor_id]
                next_targets = summary.get(edge.subtype)
                if not next_targets and (not SxS or edge.subtype != next_edge):
                    continue
                if not SxS:
                    targets[successor.name] |= set(next_targets)
                heappush(services, ((1 / successor.priority, successor.id)))
                edge_state = ("Done",) if SxS else (len(next_targets), "increment")
                run.write_state(f"edges/{edge_id}", *edge_state, top_level=True)
        if SxS:
            results = {"success": end.id in visited}
        else:
            failed = list(targets[start.name] - targets[end.name])
            summary = {"success": list(targets[end.name]), "failure": failed}
            results = {"success": not failed, "summary": summary}
        return results


class WorkflowForm(ServiceForm):
    form_type = HiddenField(default="workflow")
    category = SelectField("Category")
    close_connection = BooleanField(default=False)
    run_method = SelectField(
        "Run Method",
        choices=(
            ("per_device", "Run the workflow device by device"),
            (
                "per_service_with_workflow_targets",
                "Run the workflow service by service using workflow targets",
            ),
            (
                "per_service_with_service_targets",
                "Run the workflow service by service using service targets",
            ),
        ),
        no_search=True,
    )
    superworkflow = InstanceField(
        "Superworkflow",
        constraints={"children": ["[Shared] Placeholder"], "children_filter": "union"},
    )

    def validate(self, **_):
        valid_form = super().validate()
        invalid_superworkflow = str(self.id.data) == str(self.superworkflow.data)
        if invalid_superworkflow:
            self.superworkflow.errors.append(
                "You cannot set a workflow to be its own superworkflow."
            )
        invalid_targets_error = (
            self.run_method.data == "per_service_with_service_targets"
            and (
                self.target_devices.data
                or self.target_pools.data
                or self.device_query.data
            )
        )
        if invalid_targets_error:
            self.run_method.errors.append(
                (
                    "The workflow has device targets but the "
                    "run method is set to 'Service by Service'."
                )
            )
        return valid_form and not any(
            [
                invalid_superworkflow,
                invalid_targets_error,
            ]
        )


class WorkflowEdge(AbstractBase):
    __tablename__ = type = class_type = "workflow_edge"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    creation_time = db.Column(db.TinyString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
    soft_deleted = db.Column(Boolean, default=False)
    label = db.Column(db.SmallString)
    color = db.Column(db.SmallString)
    subtype = db.Column(db.SmallString)
    source_id = db.Column(Integer, ForeignKey("service.id"))
    source = relationship(
        "Service",
        primaryjoin="Service.id == WorkflowEdge.source_id",
        backref=backref("destinations", cascade="all, delete-orphan"),
        foreign_keys="WorkflowEdge.source_id",
    )
    destination_id = db.Column(Integer, ForeignKey("service.id"))
    destination = relationship(
        "Service",
        primaryjoin="Service.id == WorkflowEdge.destination_id",
        backref=backref("sources", cascade="all, delete-orphan"),
        foreign_keys="WorkflowEdge.destination_id",
    )
    workflow_id = db.Column(Integer, ForeignKey("workflow.id", ondelete="SET NULL"))
    workflow = relationship(
        "Workflow",
        back_populates="edges",
        foreign_keys="WorkflowEdge.workflow_id",
    )
    logs = relationship("Changelog", back_populates="workflow_edge")
    __table_args__ = (
        UniqueConstraint(subtype, source_id, destination_id, workflow_id),
    )

    def __init__(self, **kwargs):
        self.label = kwargs["subtype"]
        self.color = "green" if kwargs["subtype"] == "success" else "red"
        super().__init__(**kwargs)

    def update(self, **kwargs):
        super().update(**kwargs)
        self.set_name(kwargs.get("name"))

    def set_name(self, name=None):
        self.name = name or f"[{self.workflow}] {vs.get_time()}"
