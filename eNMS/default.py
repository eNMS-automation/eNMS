from flask import Flask

from eNMS.extensions import db
from eNMS.classes import classes
from eNMS.functions import factory, integrity_rollback, fetch, get_one
from eNMS.properties import parameters_public_properties


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


def create_default_pools() -> None:
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
        factory("Pool", **pool)


@integrity_rollback
def create_default_parameters(app: Flask) -> None:
    parameters = classes["Parameters"]()
    parameters.update(
        **{
            property: app.config[property.upper()]
            for property in parameters_public_properties
            if property.upper() in app.config
        }
    )
    db.session.add(parameters)
    db.session.commit()


def create_default_services() -> None:
    admin = fetch("User", name="admin").id
    for service in (
        {
            "type": "SwissArmyKnifeService",
            "name": "Start",
            "description": "Start point of a workflow",
            "creator": admin,
            "hidden": True,
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "End",
            "description": "End point of a workflow",
            "creator": admin,
            "hidden": True,
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "mail_feedback_notification",
            "description": "Mail notification (service logs)",
            "creator": admin,
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "slack_feedback_notification",
            "description": "Slack notification (service logs)",
            "creator": admin,
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "mattermost_feedback_notification",
            "description": "Mattermost notification (service logs)",
            "creator": admin,
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "cluster_monitoring",
            "description": "Monitor eNMS cluster",
            "creator": admin,
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "git_push_configurations",
            "description": "Push configurations to Gitlab",
            "creator": admin,
        },
        {
            "type": "SwissArmyKnifeService",
            "name": "poller_service",
            "description": "Configuration Management Poller",
            "creator": admin,
            "hidden": True,
        },
    ):
        factory(service.pop("type"), **service)


def create_default_workflows() -> None:
    name = "Configuration Management Workflow"
    workflow = factory(
        "Workflow",
        **{
            "name": name,
            "description": "Poll configuration and push to gitlab",
            "use_workflow_targets": False,
            "creator": fetch("User", name="admin").id,
        },
    )
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


def create_default_tasks(app: Flask) -> None:
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
            "is_active": app.config["CLUSTER"],
        },
    ]
    for task in tasks:
        if not fetch("Task", name=task["name"]):
            factory("Task", **task)


def create_default(app: Flask) -> None:
    create_default_parameters(app)
    parameters = get_one("Parameters")
    create_default_users()
    create_default_pools()
    create_default_services()
    create_default_workflows()
    create_default_tasks(app)
    parameters.trigger_active_parameters(app)
    db.session.commit()
