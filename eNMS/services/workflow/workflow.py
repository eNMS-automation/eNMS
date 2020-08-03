from collections import defaultdict
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import UniqueConstraint

from eNMS.database import db
from eNMS.models.base import AbstractBase
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import BooleanField, HiddenField, InstanceField, SelectField
from eNMS.models.automation import Service


@db.set_custom_properties
class Workflow(Service):

    __tablename__ = "workflow"
    pretty_name = "Workflow"
    parent_type = "service"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    close_connection = db.Column(Boolean, default=False)
    labels = db.Column(db.Dict, info={"log_change": False})
    services = relationship(
        "Service", secondary=db.service_workflow_table, back_populates="workflows"
    )
    edges = relationship(
        "WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan"
    )
    superworkflow_id = db.Column(
        Integer, ForeignKey("workflow.id", ondelete="SET NULL")
    )
    superworkflow = relationship(
        "Workflow", remote_side=[id], foreign_keys="Workflow.superworkflow_id"
    )

    __mapper_args__ = {"polymorphic_identity": "workflow"}

    def __init__(self, **kwargs):
        start = db.fetch("service", scoped_name="Start")
        end = db.fetch("service", scoped_name="End")
        self.services.extend([start, end])
        super().__init__(**kwargs)
        if self.name not in end.positions:
            end.positions[self.name] = (500, 0)

    def delete(self):
        for service in self.services:
            if not service.shared:
                db.delete("service", id=service.id)

    def set_name(self, name=None):
        old_name = self.name
        super().set_name(name)
        for service in self.services:
            if not service.shared:
                service.set_name()
            if old_name in service.positions:
                service.positions[self.name] = service.positions[old_name]

    def duplicate(self, workflow=None, clone=None):
        if not clone:
            clone = super().duplicate(workflow)
        clone_services = {}
        db.session.commit()
        for service in self.services:
            if service.shared:
                service_clone = service
                if service not in clone.services:
                    clone.services.append(service)
            else:
                service_clone = service.duplicate(clone)
            service_clone.positions[clone.name] = service.positions.get(
                self.name, (0, 0)
            )
            clone_services[service.id] = service_clone
        db.session.commit()
        for edge in self.edges:
            clone.edges.append(
                db.factory(
                    "workflow_edge",
                    **{
                        "workflow": clone.id,
                        "subtype": edge.subtype,
                        "source": clone_services[edge.source.id].id,
                        "destination": clone_services[edge.destination.id].id,
                    },
                )
            )
            db.session.commit()
        return clone

    @property
    def deep_services(self):
        services = [
            service.deep_services if service.type == "workflow" else [service]
            for service in self.services
        ]
        return [self] + sum(services, [])

    @property
    def deep_edges(self):
        return sum([w.edges for w in self.deep_services if w.type == "workflow"], [])

    def job(self, run, *args):
        if run.run_method == "per_service_with_workflow_targets":
            return self.tracking_bfs(run, *args)
        else:
            return self.standard_bfs(run, *args)

    def tracking_bfs(self, run, payload):
        number_of_runs = defaultdict(int)
        start = db.fetch("service", scoped_name="Start")
        end = db.fetch("service", scoped_name="End")
        services = [db.fetch("service", id=id) for id in run.start_services]
        visited, success, targets = set(), False, defaultdict(set)
        restart_run = run.restart_run
        for service in services:
            targets[service.name] |= {device.name for device in run.devices}
        while services:
            if run.stop:
                return {"payload": payload, "success": False}
            service = services.pop()
            if number_of_runs[service.name] >= service.maximum_runs or any(
                node not in visited
                for node, _ in service.adjacent_services(self, "source", "prerequisite")
            ):
                continue
            number_of_runs[service.name] += 1
            visited.add(service)
            if service in (start, end) or service.skip:
                results = {
                    "summary": {"success": targets[service.name], "failure": []},
                    "success": True,
                }
            else:
                kwargs = {
                    "devices": [
                        db.fetch("device", name=name).id
                        for name in targets[service.name]
                    ],
                    "service": run.placeholder.id
                    if service.scoped_name == "Placeholder"
                    else service.id,
                    "workflow": self.id,
                    "restart_run": restart_run,
                    "parent": run,
                    "parent_runtime": run.parent_runtime,
                }
                if run.parent_device_id:
                    kwargs["parent_device"] = run.parent_device_id
                service_run = db.factory("run", commit=True, **kwargs)
                results = service_run.run(payload)
            if service.run_method in ("once", "per_service_with_service_targets"):
                edge_type = "success" if results["success"] else "failure"
                for successor, edge in service.adjacent_services(
                    self, "destination", edge_type
                ):
                    targets[successor.name] |= targets[service.name]
                    services.append(successor)
                    run.write_state(
                        f"edges/{edge.id}", len(targets[service.name]), "increment"
                    )
            else:
                summary = results.get("summary", {})
                for edge_type in ("success", "failure"):
                    for successor, edge in service.adjacent_services(
                        self, "destination", edge_type,
                    ):
                        if not summary[edge_type]:
                            continue
                        targets[successor.name] |= set(summary[edge_type])
                        services.append(successor)
                        run.write_state(
                            f"edges/{edge.id}", len(summary[edge_type]), "increment"
                        )
        success_devices = targets[end.name]
        failure_devices = targets[start.name] - success_devices
        success = not failure_devices
        summary = {
            "success": list(success_devices),
            "failure": list(failure_devices),
        }
        run.write_state("progress/device/success", len(success_devices))
        run.write_state("progress/device/failure", len(failure_devices))
        db.session.refresh(run)
        run.restart_run = restart_run
        return {"payload": payload, "success": success, "summary": summary}

    def standard_bfs(self, run, payload, device=None):
        number_of_runs = defaultdict(int)
        start = db.fetch("service", scoped_name="Start")
        end = db.fetch("service", scoped_name="End")
        services = [db.fetch("service", id=id) for id in run.start_services]
        restart_run = run.restart_run
        visited = set()
        while services:
            if run.stop:
                return {"payload": payload, "success": False}
            service = services.pop()
            if number_of_runs[service.name] >= service.maximum_runs or any(
                node not in visited
                for node, _ in service.adjacent_services(self, "source", "prerequisite")
            ):
                continue
            number_of_runs[service.name] += 1
            visited.add(service)
            if service in (start, end):
                results = {"result": "skipped", "success": True}
            else:
                kwargs = {
                    "service": run.placeholder.id
                    if service.scoped_name == "Placeholder"
                    else service.id,
                    "workflow": self.id,
                    "restart_run": restart_run,
                    "parent": run,
                    "parent_runtime": run.parent_runtime,
                }
                if run.parent_device_id:
                    kwargs["parent_device"] = run.parent_device_id
                if device:
                    kwargs["devices"] = [device.id]
                service_run = db.factory("run", commit=True, **kwargs)
                results = service_run.run(payload)
            if not device:
                status = "success" if results["success"] else "failure"
                run.write_state(f"progress/service/{status}", 1, "increment")
            for successor, edge in service.adjacent_services(
                self, "destination", "success" if results["success"] else "failure",
            ):
                services.append(successor)
                if device:
                    run.write_state(f"edges/{edge.id}", 1, "increment")
                else:
                    run.write_state(f"edges/{edge.id}", "DONE")
        db.session.refresh(run)
        run.restart_run = restart_run
        return {"payload": payload, "success": end in visited}


class WorkflowForm(ServiceForm):
    form_type = HiddenField(default="workflow")
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
    )
    superworkflow = InstanceField("Superworkflow")


class WorkflowEdge(AbstractBase):

    __tablename__ = type = "workflow_edge"
    id = db.Column(Integer, primary_key=True)
    label = db.Column(db.SmallString)
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
    workflow_id = db.Column(Integer, ForeignKey("workflow.id"))
    workflow = relationship(
        "Workflow", back_populates="edges", foreign_keys="WorkflowEdge.workflow_id"
    )
    __table_args__ = (
        UniqueConstraint(subtype, source_id, destination_id, workflow_id),
    )

    def __init__(self, **kwargs):
        self.label = kwargs["subtype"]
        super().__init__(**kwargs)

    @property
    def name(self):
        return (
            f"Edge from '{self.source.name}' to '{self.destination}'"
            f" in {self.workflow.name}"
        )
