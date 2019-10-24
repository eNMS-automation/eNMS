from collections import defaultdict
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import backref, relationship
from time import sleep
from wtforms import BooleanField, HiddenField

from eNMS.database import Session
from eNMS.database.base import AbstractBase
from eNMS.database.dialect import Column, MutableDict, SmallString
from eNMS.database.functions import factory, fetch
from eNMS.database.associations import (
    service_workflow_table,
    start_services_workflow_table,
)
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import MultipleInstanceField
from eNMS.models.automation import Service


class Workflow(Service):

    __tablename__ = "workflow"
    pretty_name = "Workflow"
    parent_type = "service"
    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    close_connection = Column(Boolean, default=False)
    labels = Column(MutableDict)
    services = relationship(
        "Service", secondary=service_workflow_table, back_populates="workflows"
    )
    edges = relationship(
        "WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan"
    )
    start_services = relationship(
        "Service", secondary=start_services_workflow_table, backref="start_workflows"
    )

    __mapper_args__ = {"polymorphic_identity": "workflow"}

    def __init__(self, **kwargs):
        start = fetch("service", scoped_name="Start")
        end = fetch("service", scoped_name="End")
        self.services.extend([start, end])
        super().__init__(**kwargs)

    def set_name(self, name=None):
        old_name = self.name
        super().set_name(name)
        for service in self.services:
            service.set_name()
            service.positions[self.name] = service.positions.pop(old_name, (0, 0))

    def duplicate(self, workflow=None):
        clone = super().duplicate(workflow)
        clone_services = {}
        Session.commit()
        for service in self.services:
            if service.shared:
                service_clone = service
                if service not in clone.services:
                    clone.services.append(service)
            else:
                service_clone = service.duplicate(clone)
            service_clone.positions[clone.name] = service.positions[self.name]
            clone_services[service.id] = service_clone
        Session.commit()
        for edge in self.edges:
            clone.edges.append(
                factory(
                    "workflow_edge",
                    **{
                        "workflow": clone.id,
                        "subtype": edge.subtype,
                        "source": clone_services[edge.source.id].id,
                        "destination": clone_services[edge.destination.id].id,
                    },
                )
            )
            Session.commit()
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

    def job(self, run, payload, device=None):
        number_of_runs = defaultdict(int)
        if "start_services" in run.properties:
            services = [fetch("service", id=service) for service in run.start_services]
        else:
            services = list(run.start_services)
        visited, success = set(), False
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
            skip_service = False
            if service.skip_query:
                skip_service = run.eval(service.skip_query, **locals())
            if skip_service or service.skip:
                service_results = {"success": "skipped"}
                run.run_state["progress"]["service"]["skipped"] += 1
            else:
                kwargs = {
                    "service": service.id,
                    "workflow": self.id,
                    "parent_runtime": run.parent_runtime,
                    "restart_run": run.restart_run,
                }
                if device:
                    kwargs["devices"] = [device.id]
                service_run = factory("run", **kwargs)
                service_results = service_run.run(payload)
                status = "passed" if service_results["success"] else "failed"
                if not device:
                    run.run_state["progress"]["service"][status] += 1
            successors = []
            for successor, edge in service.adjacent_services(
                self,
                "destination",
                "success" if service_results["success"] else "failure",
            ):
                successors.append(successor)
                run.run_state["edges"][edge.id] += 1
            for successor in successors:
                services.append(successor)
                if successor == self.services[1]:
                    success = True
            if not skip_service and not service.skip:
                sleep(service.waiting_time)
        Session.refresh(run)
        return {"payload": payload, "success": success}


class WorkflowForm(ServiceForm):
    form_type = HiddenField(default="workflow")
    close_connection = BooleanField(default=False)
    start_services = MultipleInstanceField("Workflow Entry Point(s)")


class WorkflowEdge(AbstractBase):

    __tablename__ = type = "workflow_edge"
    id = Column(Integer, primary_key=True)
    label = Column(SmallString)
    subtype = Column(SmallString)
    source_id = Column(Integer, ForeignKey("service.id"))
    source = relationship(
        "Service",
        primaryjoin="Service.id == WorkflowEdge.source_id",
        backref=backref("destinations", cascade="all, delete-orphan"),
        foreign_keys="WorkflowEdge.source_id",
    )
    destination_id = Column(Integer, ForeignKey("service.id"))
    destination = relationship(
        "Service",
        primaryjoin="Service.id == WorkflowEdge.destination_id",
        backref=backref("sources", cascade="all, delete-orphan"),
        foreign_keys="WorkflowEdge.destination_id",
    )
    workflow_id = Column(Integer, ForeignKey("workflow.id"))
    workflow = relationship(
        "Workflow", back_populates="edges", foreign_keys="WorkflowEdge.workflow_id"
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
