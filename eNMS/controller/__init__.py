from uuid import getnode

from eNMS.controller.administration import AdministrationController
from eNMS.controller.automation import AutomationController
from eNMS.controller.inventory import InventoryController
from eNMS.database import Session
from eNMS.database.functions import factory, fetch
from eNMS.models import models, model_properties


class Controller(AdministrationController, AutomationController, InventoryController):
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
        if not fetch("User", allow_none=True, name="admin"):
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
                "link_name_match": "regex",
            },
            {
                "name": "Links only",
                "description": "Links only",
                "device_name": "^$",
                "device_name_match": "regex",
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
            assert isinstance(service, dict)
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
        Session.commit()
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
                "is_active": self.cluster,
            },
        ]
        for task in tasks:
            if not fetch("Task", allow_none=True, name=task["name"]):
                factory("Task", **task)

    def init_parameters(self) -> None:
        parameters = Session.query(models["Parameters"]).one_or_none()
        if not parameters:
            parameters = models["Parameters"]()
            parameters.update(
                **{
                    property: getattr(self, property)
                    for property in model_properties["Parameters"]
                    if hasattr(self, property)
                }
            )
            Session.add(parameters)
            Session.commit()
        else:
            for parameter in parameters.get_properties():
                setattr(self, parameter, getattr(parameters, parameter))

    def create_example_pools(self) -> None:
        for pool in (
            {
                "name": "Datacenter San Francisco",
                "description": "Datacenter San Francisco",
                "device_name": "e",
                "longitude": -122.43,
                "latitude": 37.77,
            },
            {
                "name": "Datacenter New York",
                "description": "Datacenter New York",
                "device_name": "a",
                "longitude": -74.0,
                "latitude": 40.71,
            },
            {
                "name": "Datacenter Chicago",
                "description": "Datacenter Chicago",
                "device_name": "i",
                "longitude": -87.62,
                "latitude": 41.87,
            },
        ):
            factory("Pool", **pool)

    def create_network_topology(self) -> None:
        with open(self.path / "projects" / "spreadsheets" / "usa.xls", "rb") as file:
            self.topology_import(file)

    def create_example_services(self) -> None:
        for service in (
            {
                "type": "ExampleService",
                "name": "Example1",
                "description": "Example",
                "devices": [fetch("Device", name="Washington").id],
                "string1": "cisco",
                "string2": "s2",
                "mail_address": "aaa@gmail.com",
                "ip_address": "10.1.1.1",
                "mac_address": "FF:FF:FF:FF:FF:FF",
                "an_integer": 10,
                "number_in_range": 7,
                "regex": "abbbbcc",
                "exclusion_field": "d",
                "url": "https://www.google.fr/",
                "a_float": 5.0,
                "a_list": ["a", "b"],
                "a_dict": {},
                "boolean1": True,
                "boolean2": False,
            },
            {
                "type": "ConfigureBgpService",
                "name": "napalm_configure_bgp_1",
                "description": "Configure BGP Peering with Napalm",
                "devices": [fetch("Device", name="Washington").id],
                "local_as": 100,
                "loopback": "Lo100",
                "loopback_ip": "100.1.1.1",
                "neighbor_ip": "100.1.2.1",
                "remote_as": 200,
                "vrf_name": "configure_BGP_test",
                "waiting_time": 0,
            },
            {
                "type": "GenericFileTransferService",
                "name": "test_file_transfer_service",
                "description": "Test the file transfer service",
                "devices": [fetch("Device", name="Aserver").id],
                "direction": "get",
                "protocol": "scp",
                "source_file": "/media/sf_VM/eNMS/tests/file_transfer/a.bin",
                "destination_file": "/media/sf_VM/eNMS/tests/file_transfer/b.bin",
                "missing_host_key_policy": True,
            },
            {
                "type": "LogBackupService",
                "name": "test_log_backup_service",
                "description": "Test the log backup service",
                "devices": [fetch("Device", name="Aserver").id],
                "protocol": "scp",
                "destination_path": "/media/sf_VM/eNMS/tests/file_transfer",
                "delete_archive": True,
                "delete_folder": True,
            },
            {
                "type": "DatabaseBackupService",
                "name": "test_database_backup_service",
                "description": "Test the log backup service",
                "devices": [fetch("Device", name="Aserver").id],
                "protocol": "scp",
                "destination_path": "/media/sf_VM/eNMS/tests/file_transfer",
                "delete_archive": True,
                "delete_folder": True,
            },
            {
                "type": "NetmikoBackupService",
                "name": "netmiko_configuration_backup",
                "description": "Test Configuration Management",
                "devices": [fetch("Device", name="Washington").id],
                "configuration_command": "show running-config",
                "multiprocessing": True,
            },
            {
                "type": "NetmikoTextfsmExtractionService",
                "name": "netmiko_textfsm_extraction",
                "description": "Variables extraction with Netmiko/TextFSM",
                "driver": "arista_eos",
                "fast_cli": True,
                "command": "show ip route",
                "textfsm_template": (
                    "Value Filldown PROTOCOL (\S+\s\S+?|\w?)\n"
                    "Value Filldown NETWORK (\d+.\d+.\d+.\d+)\n"
                    "Value Filldown MASK (\d+)\n"
                    "Value DISTANCE (\d+)\n"
                    "Value METRIC (\d+)\n"
                    "Value DIRECT (directly)\n"
                    "Value Required NEXT_HOP (connected|\d+\.\d+\.\d+\.\d+)\n"
                    "Value INTERFACE (\S+)\n\n"
                    "Start\n"
                    "  ^\s+${PROTOCOL}\s+${NETWORK}/${MASK}\s+"
                    "(?:\[${DISTANCE}/${METRIC}\]|is\s+${DIRECT})(?:.+?)"
                    "${NEXT_HOP},\s+${INTERFACE}$$ -> Next.Record"
                ),
                "devices": [fetch("Device", name="Washington").id],
                "multiprocessing": True,
            },
            {
                "type": "NapalmBackupService",
                "name": "napalm_configuration_backup",
                "description": "Test Configuration Management",
                "devices": [fetch("Device", name="Washington").id],
                "multiprocessing": True,
            },
        ):
            factory(service.pop("type"), **service)  # type: ignore

    def create_netmiko_workflow(self) -> None:
        services = []
        devices = [
            fetch("Device", name="Washington").id,
            fetch("Device", name="Austin").id,
        ]
        for service in (
            {
                "type": "NetmikoConfigurationService",
                "name": "netmiko_create_vrf_test",
                "description": 'Create a VRF "test" with Netmiko',
                "waiting_time": 0,
                "devices": devices,
                "vendor": "Arista",
                "operating_system": "eos",
                "driver": "arista_eos",
                "global_delay_factor": 1.0,
                "content": "vrf definition test",
                "privileged_mode": True,
                "fast_cli": True,
                "timeout": 3,
            },
            {
                "type": "NetmikoValidationService",
                "name": "netmiko_check_vrf_test",
                "description": 'Check that the vrf "test" is configured',
                "waiting_time": 0,
                "devices": devices,
                "vendor": "Arista",
                "operating_system": "eos",
                "driver": "arista_eos",
                "command": "show vrf",
                "content_match": "test",
                "fast_cli": True,
                "timeout": 3,
            },
            {
                "type": "NetmikoConfigurationService",
                "name": "netmiko_delete_vrf_test",
                "description": 'Delete VRF "test"',
                "waiting_time": 1,
                "devices": devices,
                "vendor": "Arista",
                "operating_system": "eos",
                "driver": "arista_eos",
                "global_delay_factor": 1.0,
                "content": "no vrf definition test",
                "privileged_mode": True,
                "fast_cli": True,
                "timeout": 3,
            },
            {
                "type": "NetmikoValidationService",
                "name": "netmiko_check_no_vrf_test",
                "description": 'Check that the vrf "test" is NOT configured',
                "waiting_time": 0,
                "devices": devices,
                "vendor": "Arista",
                "operating_system": "eos",
                "driver": "arista_eos",
                "command": "show vrf",
                "content_match": "^((?!test)[\s\S])*$",
                "content_match_regex": True,
                "fast_cli": True,
                "timeout": 3,
                "number_of_retries": 2,
                "time_between_retries": 1,
            },
        ):
            instance = factory(service.pop("type"), **service)  # type: ignore
            services.append(instance)
        workflow = factory(
            "Workflow",
            **{
                "name": "Netmiko_VRF_workflow",
                "description": "Create and delete a VRF with Netmiko",
                "devices": devices,
                "vendor": "Arista",
                "operating_system": "eos",
            },
        )
        Session.commit()
        workflow.jobs.extend(services)
        edges = [(0, 2), (2, 3), (3, 4), (4, 5), (5, 1)]
        for x, y in edges:
            factory(
                "WorkflowEdge",
                **{
                    "name": f"{workflow.name} {x} -> {y}",
                    "workflow": workflow.id,
                    "subtype": "success",
                    "source": workflow.jobs[x].id,
                    "destination": workflow.jobs[y].id,
                },
            )
        positions = [(-20, 0), (20, 0), (0, -15), (0, -5), (0, 5), (0, 15)]
        for index, (x, y) in enumerate(positions):
            workflow.jobs[index].positions["Netmiko_VRF_workflow"] = x * 10, y * 10

    def create_yaql_iteration_workflow(self) -> None:
        devices = [
            fetch("Device", name="Washington").id,
            fetch("Device", name="Austin").id,
        ]
        services = []
        for service in (
            {
                "type": "PythonSnippetService",
                "name": "add_devices_to_payload",
                "description": "Add devices to the payload",
                "source_code": (
                    "set_var('devices', ['Washington', 'Dallas'])\n"
                    "set_var('iteration_devices',\n"
                    "{'Washington': ['Loopback101', 'Loopback15'],\n"
                    "'Austin': ['Loopback9', 'Loopback1000']})\n"
                    "save_result(True, {})"
                ),
            },
            {
                "type": "NetmikoValidationService",
                "name": "netmiko_yaql_defined_devices",
                "define_devices_from_payload": True,
                "yaql_query": "$.variables.devices",
                "query_property_type": "name",
                "vendor": "Arista",
                "operating_system": "eos",
                "driver": "arista_eos",
                "command": "show vrf",
                "content_match": "test",
                "fast_cli": True,
                "timeout": 3,
            },
        ):
            instance = factory(service.pop("type"), **service)  # type: ignore
            services.append(instance)
        factory(
            "NetmikoValidationService",
            **{
                "name": "Iterated_netmiko_service",
                "devices": devices,
                "description": "Check the iteration mechanism (interfaces)",
                "waiting_time": 0,
                "vendor": "Arista",
                "operating_system": "eos",
                "driver": "arista_eos",
                "command": "show interface {{payload['iteration_variable']}}",
                "content_match": "255.255.255.255",
                "fast_cli": True,
                "timeout": 3,
            },
        )
        Session.commit()
        for service in (
            {
                "name": "Iteration_service_simple",
                "origin_of_targets": "iteration",
                "origin_of_values": "iteration_values",
                "iterated_job": fetch("Service", name="Iterated_netmiko_service").id,
                "description": "Test the iteration mechanism (Iteration values)",
                "devices": devices,
                "iteration_values": {"Loopback11": 0, "Loopback15": 0},
            },
            {
                "name": "Iteration_service_yaql",
                "origin_of_targets": "iterated",
                "origin_of_values": "yaql",
                "yaql_query_values": "$.variables.iteration_devices",
                "per_device_values": True,
                "iterated_job": fetch("Service", name="Iterated_netmiko_service").id,
                "description": "Test the iteration mechanism (YaQL values)",
                "iteration_values": {"Loopback11": 0, "Loopback15": 0},
            },
        ):
            services.append(factory("IterationService", **service))  # type: ignore
        workflow = factory(
            "Workflow",
            **{
                "name": "YaQL_test_worflow",
                "description": "Test YaQL device selection mechanism",
                "use_workflow_targets": False,
            },
        )
        Session.commit()
        workflow.jobs.extend(services)
        edges = [(0, 2), (2, 3), (3, 4), (4, 5), (5, 1)]
        for x, y in edges:
            for edge_type in ("success", "failure"):
                factory(
                    "WorkflowEdge",
                    **{
                        "name": f"{edge_type}: {workflow.name} {x} -> {y}",
                        "workflow": workflow.id,
                        "subtype": edge_type,
                        "source": workflow.jobs[x].id,
                        "destination": workflow.jobs[y].id,
                    },
                )
        positions = [(-20, 0), (20, 0), (0, -15), (0, -5), (0, 5), (0, 15)]
        for index, (x, y) in enumerate(positions):
            workflow.jobs[index].positions["YaQL_test_worflow"] = x * 10, y * 10

    def create_napalm_workflow(self) -> None:
        devices = [
            fetch("Device", name="Washington").id,
            fetch("Device", name="Austin").id,
        ]
        services = [
            factory(
                "NapalmConfigurationService",
                **{
                    "name": "napalm_create_vrf_test",
                    "description": 'Create a VRF "test" with Napalm',
                    "waiting_time": 0,
                    "devices": devices,
                    "driver": "eos",
                    "vendor": "Arista",
                    "operating_system": "eos",
                    "action": "load_merge_candidate",
                    "content": "vrf definition test\n",
                },
            )
        ]
        services.extend(
            [
                fetch("Job", name="netmiko_check_vrf_test"),
                fetch("Job", name=f"netmiko_delete_vrf_test"),
                fetch("Job", name=f"netmiko_check_no_vrf_test"),
            ]
        )
        workflow = factory(
            "Workflow",
            **{
                "name": "Napalm_VRF_workflow",
                "description": "Create and delete a VRF with Napalm",
                "devices": devices,
                "vendor": "Arista",
                "operating_system": "eos",
            },
        )
        Session.commit()
        workflow.jobs.extend(services)
        edges = [(0, 2), (2, 3), (3, 4), (4, 5), (5, 1)]
        for x, y in edges:
            factory(
                "WorkflowEdge",
                **{
                    "name": f"{workflow.name} {x} -> {y}",
                    "workflow": workflow.id,
                    "subtype": "success",
                    "source": workflow.jobs[x].id,
                    "destination": workflow.jobs[y].id,
                },
            )
        positions = [(-20, 0), (20, 0), (0, -15), (0, -5), (0, 5), (0, 15)]
        for index, (x, y) in enumerate(positions):
            workflow.jobs[index].positions["Napalm_VRF_workflow"] = x * 10, y * 10

    def create_payload_transfer_workflow(self) -> None:
        services = []
        devices = [
            fetch("Device", name="Washington").id,
            fetch("Device", name="Austin").id,
        ]
        for service in (
            [
                {
                    "name": "GET_device",
                    "has_targets": True,
                    "type": "RestCallService",
                    "description": "Use GET ReST call on eNMS ReST API",
                    "username": "admin",
                    "password": "admin",
                    "waiting_time": 0,
                    "devices": devices,
                    "validation_method": "text",
                    "content_match": "",
                    "call_type": "GET",
                    "url": "http://127.0.0.1:5000/rest/instance/device/{{device.name}}",
                    "payload": {},
                    "multiprocessing": True,
                }
            ]
            + [
                {
                    "name": f"{getter}",
                    "type": "NapalmGettersService",
                    "description": f"Getter: {getter}",
                    "waiting_time": 0,
                    "devices": devices,
                    "driver": "eos",
                    "content_match": "",
                    "getters": [getter],
                }
                for getter in (
                    "get_facts",
                    "get_interfaces",
                    "get_interfaces_ip",
                    "get_config",
                )
            ]
            + [
                {
                    "name": "process_payload1",
                    "has_targets": True,
                    "type": "SwissArmyKnifeService",
                    "description": "Process Payload in example workflow",
                    "waiting_time": 0,
                    "devices": devices,
                }
            ]
        ):
            instance = factory(service.pop("type"), **service)  # type: ignore
            services.append(instance)
        workflow = factory(
            "Workflow",
            **{
                "name": "payload_transfer_workflow",
                "description": "ReST call, Napalm getters, etc",
                "use_workflow_targets": False,
                "devices": devices,
                "vendor": "Arista",
                "operating_system": "eos",
            },
        )
        Session.commit()
        workflow.jobs.extend(services)
        positions = [
            (-20, 0),
            (50, 0),
            (-5, 0),
            (-5, -10),
            (15, 10),
            (15, -10),
            (30, -10),
            (30, 0),
        ]
        for index, (x, y) in enumerate(positions):
            job = workflow.jobs[index]
            job.positions["payload_transfer_workflow"] = x * 10, y * 10
        edges = [(0, 2), (2, 3), (2, 4), (3, 5), (5, 6), (6, 7), (4, 7), (7, 1)]
        for x, y in edges:
            factory(
                "WorkflowEdge",
                **{
                    "name": f"{workflow.name}:success {x} -> {y}",
                    "workflow": workflow.id,
                    "subtype": "success",
                    "source": workflow.jobs[x].id,
                    "destination": workflow.jobs[y].id,
                },
            )
        prerequisite_edges = [(4, 7), (3, 7)]
        for x, y in prerequisite_edges:
            factory(
                "WorkflowEdge",
                **{
                    "name": f"{workflow.name}:prerequisite {x} -> {y}",
                    "workflow": workflow.id,
                    "subtype": "prerequisite",
                    "source": workflow.jobs[x].id,
                    "destination": workflow.jobs[y].id,
                },
            )

    def create_workflow_of_workflows(self) -> None:
        devices = [fetch("Device", name="Washington").id]
        workflow = factory(
            "Workflow",
            **{
                "name": "Workflow_of_workflows",
                "description": "Test the inner workflow system",
                "devices": devices,
                "vendor": "Arista",
                "operating_system": "eos",
            },
        )
        Session.commit()
        workflow.jobs.extend(
            [
                fetch("Job", name="payload_transfer_workflow"),
                fetch("Job", name="get_interfaces"),
                fetch("Job", name="Napalm_VRF_workflow"),
            ]
        )
        edges = [(0, 2), (2, 3), (3, 4), (4, 1)]
        for x, y in edges:
            factory(
                "WorkflowEdge",
                **{
                    "name": f"{workflow.name} {x} -> {y}",
                    "workflow": workflow.id,
                    "subtype": "success",
                    "source": workflow.jobs[x].id,
                    "destination": workflow.jobs[y].id,
                },
            )
        positions = [(-30, 0), (30, 0), (0, -20), (0, 0), (0, 20)]
        for index, (x, y) in enumerate(positions):
            workflow.jobs[index].positions["Workflow_of_workflows"] = x * 10, y * 10

    def create_default(self) -> None:
        self.init_parameters()
        self.configure_server_id()
        self.create_default_users()
        self.create_default_pools()
        self.create_default_services()
        Session.commit()
        self.create_default_workflows()
        Session.commit()
        self.create_default_tasks()
        self.get_git_content()

    def examples_creation(self) -> None:
        self.create_example_pools()
        self.create_network_topology()
        Session.commit()
        self.create_example_services()
        self.create_netmiko_workflow()
        self.create_napalm_workflow()
        self.create_payload_transfer_workflow()
        self.create_yaql_iteration_workflow()
        self.create_workflow_of_workflows()
        Session.commit()

    def init_database(self) -> None:
        self.create_default()
        if self.create_examples:
            self.examples_creation()


controller = Controller()
