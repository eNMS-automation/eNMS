from orjson import dumps
from pathlib import Path
from random import choice, randrange

PATH = (
    Path.cwd().parent.parent.parent
    / "eNMS-prod2"
    / "files"
    / "migrations"
    / "scalability"
)


def generate_devices():
    with open(PATH / "generic_device.json", "wb") as file:
        file.write(
            dumps(
                [
                    {"name": f"Device{index}", "model": f"Model{randrange(1, 21)}"}
                    for index in range(150_000)
                ]
            )
        )


def generate_links():
    with open(PATH / "generic_link.json", "wb") as file:
        file.write(
            dumps(
                [
                    {"name": f"Link{index}", "model": f"Model{randrange(1, 51)}"}
                    for index in range(30_000)
                ]
            )
        )


def generate_services():
    with open(PATH / "swiss_army_knife_service.json", "wb") as file:
        file.write(
            dumps(
                [
                    {
                        "name": "[Shared] Start",
                        "scoped_name": "Start",
                        "shared": True,
                    },
                    {
                        "name": "[Shared] End",
                        "scoped_name": "End",
                        "shared": True,
                    },
                    {
                        "name": "[Shared] Placeholder",
                        "scoped_name": "Placeholder",
                        "shared": True,
                    },
                ]
            )
        )
    with open(PATH / "python_snippet_service.json", "wb") as file:
        file.write(
            dumps(
                [
                    {
                        "persistent_id": f"Service{index}",
                        "name": f"[Shared] Service{index}",
                        "model": f"Model{randrange(1, 21)}",
                        "vendor": ["Cisco", "Juniper", "Arista"][index % 3],
                        "source_code": 'results["success"] = True',
                        "scoped_name": f"Service{index}",
                        "shared": True,
                    }
                    for index in range(9_997)
                ]
            )
        )


def generate_workflows():
    workflows = []
    for index in range(2_000):
        positions = {"[Shared] Start": [0, 0], "[Shared] End": [2200, 400]}
        for i in range(10):
            positions[f"[Shared] Service{index + i}"] = ((i + 1) * 200, 0)
            positions[f"[Shared] Service{index + i + 10}"] = (2000 - 200 * i, 200)
            positions[f"[Shared] Service{index + i + 20}"] = ((i + 1) * 200, 400)
        workflows.append(
            {
                "persistent_id": f"Workflow{index}",
                "builder_link": f"Workflow{index}",
                "name": f"[Shared] Workflow{index}",
                "positions": positions,
                "vendor": ["Cisco", "Juniper", "Arista"][index % 3],
                "scoped_name": f"Workflow{index}",
                "shared": True,
            }
        )
    with open(PATH / "workflow.json", "wb") as file:
        file.write(dumps(workflows))


def generate_workflow_association_table():
    association_table = []
    for j in range(2_000):
        association_table.append(["[Shared] Start", f"[Shared] Workflow{j}"])
        association_table.append(["[Shared] End", f"[Shared] Workflow{j}"])
        for i in range(j, j + 30):
            association_table.append([f"[Shared] Service{i}", f"[Shared] Workflow{j}"])
    with open(PATH / "service_workflow_table.json", "wb") as file:
        file.write(dumps(association_table))


def generate_service_target_table():
    with open(PATH / "service_target_pool_table.json", "wb") as file:
        file.write(dumps([[f"[Shared] Service{i}", "Pool0"] for i in range(9_997)]))
    with open(PATH / "service_target_device_table.json", "wb") as file:
        device_targets = []
        for i in range(2_000):
            if i in (2, 3):
                continue
            for j in range(100):
                device_targets.append([f"[Shared] Workflow{i}", f"Device{j}"])
        for j in range(1_000):
            device_targets.append(["[Shared] Workflow2", f"Device{j}"])
        for j in range(10_000):
            device_targets.append(["[Shared] Workflow3", f"Device{j}"])
        file.write(dumps(device_targets))


def generate_tasks():
    with open(PATH / "task.json", "wb") as file:
        file.write(
            dumps(
                [
                    {"name": f"Task{index}", "is_active": choice([True, False])}
                    for index in range(2_000)
                ]
            )
        )


def generate_task_service():
    with open(PATH / "task_service.json", "wb") as file:
        file.write(
            dumps(
                {
                    f"Task{index}": f"[Shared] Workflow{index // 10}"
                    for index in range(2_000)
                }
            )
        )


def generate_pools():
    pools = []
    for index in range(2_000):
        if index < 1_000:
            pools.append({"name": f"Pool{index}", "manually_defined": True})
        else:
            start_range = randrange(1, 150)
            pools.append(
                {
                    "name": f"Pool{index}",
                    "device_name": f"Device{start_range}\\d{{3}}",
                    "device_name_match": "regex",
                }
            )
    with open(PATH / "pool.json", "wb") as file:
        file.write(dumps(pools))


def generate_pool_association_table():
    association_table = [
        [f"Pool{j}", f"Device{i}"]
        for j in range(1000)
        for i in range(j * 100, j * 100 + 100)
    ]
    with open(PATH / "pool_device_table.json", "wb") as file:
        file.write(dumps(association_table))


def generate_users():
    password = (
        "JGFyZ29uMmlkJHY9MTkkbT0xMDI0MDAsdD0yLHA9OCRNaWFrOVA3Z"
        "it6OW5qSEd1RmVLOGR3JEhLWk5VWnVpMnlObkt5QnRHNFR4WEE="
    )
    users = [{"name": "admin", "is_admin": True, "password": password}]
    for i in range(1, 1000):
        users.append({"name": f"User{i}", "is_admin": i < 100, "password": password})
    with open(PATH / "user.json", "wb") as file:
        file.write(dumps(users))


def generate_workflow_edges():
    workflow_edges = []
    workflow_edge_source = {}
    workflow_edge_destination = {}
    workflow_edge_workflow = {}
    edge_kwargs = {"subtype": "success", "label": "success", "color": "green"}
    for j in range(2000):
        # Edge from Start
        workflow_edges.append({"name": f"Start Edge {j}", **edge_kwargs})
        workflow_edge_source[f"Start Edge {j}"] = "[Shared] Start"
        workflow_edge_destination[f"Start Edge {j}"] = f"[Shared] Service{j}"
        workflow_edge_workflow[f"Start Edge {j}"] = f"[Shared] Workflow{j}"
        # Edge to End
        workflow_edges.append({"name": f"End Edge {j}", **edge_kwargs})
        workflow_edge_source[f"End Edge {j}"] = f"[Shared] Service{j + 29}"
        workflow_edge_destination[f"End Edge {j}"] = "[Shared] End"
        workflow_edge_workflow[f"End Edge {j}"] = f"[Shared] Workflow{j}"
        for i in range(j, j + 29):
            # Edge between Services
            workflow_edges.append({"name": f"Edge {j} - {i}", **edge_kwargs})
            workflow_edge_source[f"Edge {j} - {i}"] = f"[Shared] Service{i}"
            workflow_edge_destination[f"Edge {j} - {i}"] = f"[Shared] Service{i + 1}"
            workflow_edge_workflow[f"Edge {j} - {i}"] = f"[Shared] Workflow{j}"
    with open(PATH / "workflow_edge.json", "wb") as file:
        file.write(dumps(workflow_edges))
    with open(PATH / "workflow_edge_source.json", "wb") as file:
        file.write(dumps(workflow_edge_source))
    with open(PATH / "workflow_edge_destination.json", "wb") as file:
        file.write(dumps(workflow_edge_destination))
    with open(PATH / "workflow_edge_workflow.json", "wb") as file:
        file.write(dumps(workflow_edge_workflow))


def generate_servers():
    servers = [
        {
            "name": "eNMS Server",
            "allowed_automation": ["scheduler", "rest_api", "application"],
        }
    ] + [{"name": f"Server{i}"} for i in range(1, 1_000)]
    with open(PATH / "server.json", "wb") as file:
        file.write(dumps(servers))


def generate_runs():
    runs = []
    run_service = {}
    run_service_table = []
    for index in range(1000):
        runtime = f"2000-00-00 00:00:00.{index}"
        inner_state = {
            "success": True,
            "status": "Running",
            "result": {"runtime": runtime, "success": True},
            "progress": {"device": {"total": 1, "success": 1}},
        }
        state = {"Workflow0": inner_state}
        run_service_table.append([runtime, "[Shared] Workflow0"])
        for service_index in range(30):
            state[f"Workflow0>Service{service_index}"] = inner_state
            run_service_table.append([runtime, f"[Shared] Service{service_index}"])
        runs.append(
            {
                "name": runtime,
                "creator": "admin",
                "success": True,
                "status": "Completed",
                "runtime": runtime,
                "duration": "0:00:01",
                "path": "Workflow0",
                "state": state,
            }
        )
        run_service[runtime] = "[Shared] Workflow0"
    for index in range(1000, 10000):
        runtime = f"1000-00-00 00:00:00.{index}"
        runs.append(
            {
                "name": runtime,
                "creator": "admin",
                "success": True,
                "status": "Completed",
                "runtime": runtime,
                "duration": "0:00:01",
                "path": "Workflow1",
            }
        )
        run_service[runtime] = "[Shared] Workflow1"
        run_service_table.append([runtime, "[Shared] Workflow1"])
    with open(PATH / "run.json", "wb") as file:
        file.write(dumps(runs))
    with open(PATH / "run_service.json", "wb") as file:
        file.write(dumps(run_service))
    with open(PATH / "run_service_table.json", "wb") as file:
        file.write(dumps(run_service_table))


def generate_results():
    results = []
    result_workflow = {}
    result_service = {}
    result_run = {}
    result_device = {}
    for run in range(1000):
        runtime = f"2000-00-00 00:00:00.{run}"
        for service in range(30):
            for device in range(10):
                result_name = f"Run{run} - Service{service} - Device{device}"
                result_workflow[result_name] = "[Shared] Workflow0"
                result_service[result_name] = f"[Shared] Service{service}"
                result_run[result_name] = runtime
                result_device[result_name] = f"Device{device}"
                results.append(
                    {
                        "name": result_name,
                        "path": f"Workflow0>Service{service}",
                        "success": True,
                        "runtime": runtime,
                        "result": {
                            "runtime": runtime,
                            "success": True,
                        },
                        "parent_runtime": runtime,
                    }
                )
    with open(PATH / "result.json", "wb") as file:
        file.write(dumps(results))
    with open(PATH / "result_workflow.json", "wb") as file:
        file.write(dumps(result_workflow))
    with open(PATH / "result_service.json", "wb") as file:
        file.write(dumps(result_service))
    with open(PATH / "result_run.json", "wb") as file:
        file.write(dumps(result_run))
    with open(PATH / "result_device.json", "wb") as file:
        file.write(dumps(result_device))


def generate_networks():
    pass


generate_service_target_table()
