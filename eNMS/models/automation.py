from sqlalchemy import Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from eNMS import app
from eNMS.database.dialect import Column, LargeString, MutableDict, SmallString
from eNMS.database.associations import (
    service_device_table,
    service_event_table,
    service_pool_table,
    service_workflow_table,
)
from eNMS.database.base import AbstractBase
from eNMS.models.inventory import Device  # noqa: F401
from eNMS.models.execution import Run  # noqa: F401
from eNMS.models.events import Task  # noqa: F401
from eNMS.models.administration import User  # noqa: F401


class Service(AbstractBase):

    __tablename__ = "service"
    type = Column(SmallString)
    __mapper_args__ = {"polymorphic_identity": "service", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    hidden = Column(Boolean, default=False)
    name = Column(SmallString, unique=True)
    reference_name = Column(SmallString)
    last_modified = Column(SmallString)
    description = Column(SmallString)
    number_of_retries = Column(Integer, default=0)
    time_between_retries = Column(Integer, default=10)
    positions = Column(MutableDict)
    tasks = relationship("Task", back_populates="service", cascade="all,delete")
    vendor = Column(SmallString)
    operating_system = Column(SmallString)
    waiting_time = Column(Integer, default=0)
    creator = Column(SmallString, default="admin")
    push_to_git = Column(Boolean, default=False)
    workflows = relationship(
        "Workflow", secondary=service_workflow_table, back_populates="services"
    )
    device_query = Column(SmallString)
    device_query_property = Column(SmallString, default="ip_address")
    devices = relationship(
        "Device", secondary=service_device_table, back_populates="services"
    )
    pools = relationship(
        "Pool", secondary=service_pool_table, back_populates="services"
    )
    events = relationship(
        "Event", secondary=service_event_table, back_populates="services"
    )
    send_notification = Column(Boolean, default=False)
    send_notification_method = Column(SmallString, default="mail")
    notification_header = Column(LargeString, default="")
    display_only_failed_nodes = Column(Boolean, default=True)
    include_link_in_summary = Column(Boolean, default=True)
    mail_recipient = Column(SmallString)
    color = Column(SmallString, default="#D2E5FF")
    initial_payload = Column(MutableDict)
    skip = Column(Boolean, default=False)
    skip_query = Column(SmallString)
    iteration_values = Column(LargeString)
    iteration_variable_name = Column(SmallString, default="iteration_value")
    iteration_devices = Column(LargeString)
    iteration_devices_property = Column(SmallString, default="ip_address")
    result_postprocessing = Column(LargeString)
    runs = relationship("Run", back_populates="service", cascade="all, delete-orphan")
    maximum_runs = Column(Integer, default=1)
    multiprocessing = Column(Boolean, default=False)
    max_processes = Column(Integer, default=5)
    conversion_method = Column(SmallString, default="none")
    validation_method = Column(SmallString, default="none")
    content_match = Column(LargeString, default="")
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict)
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)

    @property
    def filename(self):
        return app.strip_all(self.name)

    def get_name(self):
        if len(self.workflows) == 1:
            workflow = f"[{self.workflows[0]}]" 
        else:
            workflow = "[Shared]" if self.workflows else ""
        return f"{workflow} {self.reference_name}" 

    def generate_row(self, table):
        return [
            f"Running" if app.service_db[self.id]["runs"] else "Idle",
            f"""
            <ul class="pagination pagination-lg" style="margin: 0px; width: 400px">
          <li>
            <button type="button" class="btn btn-info"
            onclick="showResultsPanel({self.row_properties})" data-tooltip="Results"
              ><span class="glyphicon glyphicon-list-alt"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-info"
            onclick="showLogsPanel({self.row_properties})" data-tooltip="Logs"
              ><span class="glyphicon glyphicon-list"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-success"
            onclick="normalRun('{self.id}')" data-tooltip="Run"
              ><span class="glyphicon glyphicon-play"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-success"
            onclick="showTypePanel('{self.type}', '{self.id}', 'run')"
            data-tooltip="Parametrized Run"
              ><span class="glyphicon glyphicon-play-circle"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-primary"
            onclick="showTypePanel('{self.type}', '{self.id}')" data-tooltip="Edit"
              ><span class="glyphicon glyphicon-edit"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-primary"
            onclick="showTypePanel('{self.type}', '{self.id}', 'duplicate')"
            data-tooltip="Duplicate"
              ><span class="glyphicon glyphicon-duplicate"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-primary"
            onclick="exportService('{self.id}')" data-tooltip="Export"
              ><span class="glyphicon glyphicon-download"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-danger"
            onclick="showDeletionPanel({self.row_properties})" data-tooltip="Delete"
              ><span class="glyphicon glyphicon-trash"></span
            ></button>
          </li>
        </ul>""",
        ]

    def adjacent_services(self, workflow, direction, subtype):
        for edge in getattr(self, f"{direction}s"):
            if edge.subtype == subtype and edge.workflow == workflow:
                yield getattr(edge, direction), edge


class ConnectionService(Service):

    __tablename__ = "connection_service"
    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    parent_type = "service"
    credentials = Column(SmallString, default="device")
    custom_username = Column(SmallString)
    custom_password = Column(SmallString)
    start_new_connection = Column(Boolean, default=False)
    close_connection = Column(Boolean, default=False)
    __mapper_args__ = {"polymorphic_identity": "connection_service"}
