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
from eNMS.forms.fields import MultipleInstanceField, NoValidationSelectField
from eNMS.models.automation import Service


class Workflow(Service):

    __tablename__ = "workflow"
    __mapper_args__ = {"polymorphic_identity": "workflow"}
    parent_type = "service"
    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
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

    def __init__(self, **kwargs):
        start, end = fetch("service", name="Start"), fetch("service", name="End")
        self.services.extend([start, end])
        super().__init__(**kwargs)
        if not kwargs.get("start_services"):
            self.start_services = [start]
        if self.name not in end.positions:
            end.positions[self.name] = (500, 0)

    def job(self, run, payload, device=None):
        number_of_runs = defaultdict(int)
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
                    kwargs["parent_device"] = device.id
                    kwargs["devices"] = [device.id]
                service_run = factory("run", **kwargs)
                Session.commit()
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
        return {"payload": payload, "success": success}


class WorkflowForm(ServiceForm):
    form_type = HiddenField(default="workflow")
    start_services = MultipleInstanceField("Workflow Entry Point(s)")
    restart_runtime = NoValidationSelectField("Restart Runtime", choices=())


class WorkflowEdge(AbstractBase):

    __tablename__ = type = "workflow_edge"
    id = Column(Integer, primary_key=True)
    name = Column(SmallString)
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
