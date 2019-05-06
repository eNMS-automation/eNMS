from flask import Flask
from uuid import getnode

from eNMS.controller import controller
from eNMS.database_helpers import factory, fetch, get_one, session_scope
from eNMS.models import classes, cls_to_properties


def configure_server_id(session) -> None:
    factory(
        "Server",
        session,
        **{
            "name": str(getnode()),
            "description": "Localhost",
            "ip_address": "0.0.0.0",
            "status": "Up",
        },
    )


def create_default_users() -> None:
    if not fetch("User", name="admin"):
        factory(
            "User",
            **{
                "name": "admin",
                "email": "admin@admin.com",
                "password": "admin",
                "permissions": ["Admin"],
            },
        )


def create_default_pools(session) -> None:
    for pool in (
        {"name": "All objects", "description": "All objects"},
        {
            "name": "Devices only",
            "description": "Devices only",
            "link_name": "^$",
            "link_name_regex": "y",
        },
        {
            "name": "Links only",
            "description": "Links only",
            "device_name": "^$",
            "device_name_regex": "y",
        },
    ):
        factory("Pool", session, **pool)


def create_default_parameters(app: Flask) -> None:
    if not get_one("Parameters"):
        parameters = classes["Parameters"]()
        parameters.update(
            **{
                property: controller.config[property.upper()]
                for property in cls_to_properties["Parameters"]
                if property.upper() in controller.config
            }
        )
        with session_scope() as session:
            session.add(parameters)
            session.commit()


def create_default_services(session) -> None:
    for service in (
        {
            "type": "SwissArmyKnifeService",
            "name": "Start",
            "description": "Start point of a workflow",
            "hidden": True,
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "End",
            "description": "End point of a workflow",
            "hidden": True,
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "mail_feedback_notification",
            "description": "Mail notification (service logs)",
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "slack_feedback_notification",
            "description": "Slack notification (service logs)",
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "mattermost_feedback_notification",
            "description": "Mattermost notification (service logs)",
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "cluster_monitoring",
            "description": "Monitor eNMS cluster",
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "git_push_configurations",
            "description": "Push configurations to Gitlab",
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "poller_service",
            "description": "Configuration Management Poller",
            "hidden": True,
        },
    ):
        factory(service.pop("type"), session, **service)


def create_default_workflows(session) -> None:
    name = "Configuration Management Workflow"
    workflow = factory(
        "Workflow",
        session,
        **{
            "name": name,
            "description": "Poll configuration and push to gitlab",
            "use_workflow_targets": False,
        },
    )
    session.add(workflow)
    workflow.jobs.extend(
        [
            fetch("Service", name="poller_service"),
            fetch("Service", name="git_push_configurations"),
        ]
    )
    edges = [(0, 2, True), (2, 3, True), (2, 3, False), (3, 1, True)]
    for x, y, edge_type in edges:
        factory(
            "WorkflowEdge",
            session,
            **{
                "name": f"{workflow.name} {x} -> {y} ({edge_type})",
                "workflow": workflow.id,
                "subtype": "success" if edge_type else "failure",
                "source": workflow.jobs[x].id,
                "destination": workflow.jobs[y].id,
            },
        )
    positions = [(-30, 0), (20, 0), (0, -20), (0, 30)]
    for index, (x, y) in enumerate(positions):
        workflow.jobs[index].positions[name] = x * 10, y * 10


def create_default_tasks(app: Flask, session) -> None:
    tasks = [
        {
            "aps_job_id": "Poller",
            "name": "Poller",
            "description": "Back-up device configurations",
            "job": fetch("Workflow", name="Configuration Management Workflow").id,
            "frequency": 3600,
        },
        {
            "aps_job_id": "Cluster Monitoring",
            "name": "Cluster Monitoring",
            "description": "Monitor eNMS cluster",
            "job": fetch("Service", name="cluster_monitoring").id,
            "frequency": 15,
            "is_active": controller.config["CLUSTER"],
        },
    ]
    for task in tasks:
        if not fetch("Task", name=task["name"]):
            factory("Task", session, **task)


def create_default(app: Flask) -> None:
    with session_scope() as session:
        configure_server_id(session)
        create_default_parameters(app)
        parameters = get_one("Parameters")
        create_default_users()
        create_default_pools(session)
        create_default_services(session)
        create_default_workflows(session)
        create_default_tasks(app, session)
        parameters.get_git_content(app)
        session.commit()
