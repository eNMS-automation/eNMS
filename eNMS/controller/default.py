from uuid import getnode

from eNMS.database.functions import factory, fetch, Session


class DefaultController:
    def configure_server_id(self) -> None:
        factory(
            "Server",
            **{
                "name": str(getnode()),
                "description": "Localhost",
                "ip_address": "0.0.0.0",
                "status": "Up",
            },
        )

    def create_default_users(self) -> None:
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

    def create_default_pools(self) -> None:
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

    def create_default_services(self) -> None:
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
            factory(service.pop("type"), **service)

    def create_default_workflows(self) -> None:
        name = "Configuration Management Workflow"
        workflow = factory(
            "Workflow",
            **{
                "name": name,
                "description": "Poll configuration and push to gitlab",
                "use_workflow_targets": False,
            },
        )
        Session.add(workflow)
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

    def create_default_tasks(self) -> None:
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
                "is_active": self.config["CLUSTER"],
            },
        ]
        for task in tasks:
            if not fetch("Task", name=task["name"]):
                factory("Task", **task)

    def create_default(self) -> None:
        self.configure_server_id()
        self.create_default_users()
        self.create_default_pools()
        self.create_default_services()
        Session.commit()
        self.create_default_workflows()
        Session.commit()
        self.create_default_tasks()
        self.get_git_content()
