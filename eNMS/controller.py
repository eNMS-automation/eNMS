from collections import Counter, defaultdict
from contextlib import redirect_stdout
from datetime import datetime
from difflib import unified_diff
from dramatiq import actor
from flask_login import current_user
from functools import wraps
from git import Repo
from io import BytesIO, StringIO
from ipaddress import IPv4Network
from json import dump, load
from logging import info
from operator import attrgetter, itemgetter
from os import getenv, listdir, makedirs, scandir
from os.path import exists
from pathlib import Path
from re import search, sub
from requests import get as http_get
from ruamel import yaml
from shutil import rmtree
from sqlalchemy import and_, cast, or_, String
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import true
from subprocess import Popen
from tarfile import open as open_tar
from threading import current_thread, Thread
from traceback import format_exc
from uuid import uuid4
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

from eNMS.database import db
from eNMS.forms import form_factory
from eNMS.environment import env
from eNMS.variables import vs


class Controller:
    def _initialize(self, first_init):
        if not first_init:
            return
        self.migration_import(
            name=vs.settings["app"].get("startup_migration", "default"),
            import_export_types=db.import_export_models,
        )
        self.get_git_content()
        self.scan_folder()

    def _register_endpoint(self, func):
        setattr(self, func.__name__, func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    def add_edge(self, workflow_id, subtype, source, destination):
        workflow = db.fetch("workflow", id=workflow_id, rbac="edit")
        workflow_edge = self.update(
            "workflow_edge",
            rbac=None,
            **{
                "name": vs.get_time(),
                "workflow": workflow_id,
                "subtype": subtype,
                "source": source,
                "destination": destination,
            },
        )
        workflow.update_last_modified_properties()
        db.session.commit()
        return {"update_time": workflow.last_modified, **workflow_edge}

    def add_instances_in_bulk(self, **kwargs):
        target = db.fetch(kwargs["relation_type"], id=kwargs["relation_id"])
        if target.type == "pool" and not target.manually_defined:
            return {"alert": "Adding objects to a dynamic pool is not allowed."}
        model, property = kwargs["model"], kwargs["property"]
        instances = set(db.objectify(model, kwargs["instances"]))
        if kwargs["names"]:
            for name in [instance.strip() for instance in kwargs["names"].split(",")]:
                instance = db.fetch(model, allow_none=True, name=name)
                if not instance:
                    return {"alert": f"{model.capitalize()} '{name}' does not exist."}
                instances.add(instance)
        instances = instances - set(getattr(target, property))
        for instance in instances:
            getattr(target, property).append(instance)
        target.last_modified = vs.get_time()
        target.last_modified_by = current_user.name
        return {"number": len(instances), "target": target.base_properties}

    def add_objects_to_network(self, network_id, **kwargs):
        network = db.fetch("network", id=network_id)
        result = {"nodes": [], "links": []}
        nodes = set(db.objectify("node", kwargs["nodes"]))
        links = set(db.objectify("link", kwargs["links"]))
        for pool in db.objectify("pool", kwargs["pools"]):
            nodes |= set(pool.devices) | set(pool.networks)
            links |= set(pool.links)
        if kwargs["add_connected_nodes"]:
            for link in links:
                nodes |= {link.source, link.destination}
        if kwargs["add_connected_links"]:
            for node in nodes:
                links |= set(node.get_neighbors("link"))
        for node in nodes:
            if not node or node in network.nodes or node == network:
                continue
            result["nodes"].append(node.serialized)
            network.nodes.append(node)
        for link in links:
            if link in network.links:
                continue
            if (
                link.source not in network.nodes
                or link.destination not in network.nodes
            ):
                continue
            result["links"].append(link.serialized)
            network.links.append(link)
        return result

    def bulk_deletion(self, table, **kwargs):
        instances = self.filtering(table, properties=["id"], **kwargs)
        for instance in instances:
            db.delete(table, id=instance.id)
        return len(instances)

    def bulk_edit(self, table, **kwargs):
        instances = kwargs.pop("id").split("-")
        for instance_id in instances:
            instance = db.factory(table, id=instance_id)
            for property, value in kwargs.items():
                if not kwargs.get(f"bulk-edit-{property}"):
                    continue
                edit_mode = kwargs.get(f"{property}-edit-mode")
                if not edit_mode:
                    setattr(instance, property, value)
                else:
                    current_value = getattr(instance, property)
                    related_model = vs.relationships[table][property]["model"]
                    objects = db.objectify(related_model, value)
                    if edit_mode == "set":
                        setattr(instance, property, objects)
                    else:
                        for obj in objects:
                            if edit_mode == "append" and obj not in current_value:
                                current_value.append(obj)
                            elif edit_mode == "remove" and obj in current_value:
                                current_value.remove(obj)
        return len(instances)

    def bulk_removal(
        self,
        table,
        target_type,
        target_id,
        target_property,
        **kwargs,
    ):
        target = db.fetch(target_type, id=target_id)
        if target.type == "pool" and not target.manually_defined:
            return {"alert": "Removing objects from a dynamic pool is an allowed."}
        instances = self.filtering(table, bulk="object", **kwargs)
        for instance in instances:
            getattr(target, target_property).remove(instance)
        return len(instances)

    def calendar_init(self, type):
        results, properties = {}, ["id", "name", "runtime", "service_properties"]
        for instance in db.fetch_all(type):
            if getattr(instance, "workflow", None):
                continue
            date = getattr(instance, "next_run_time" if type == "task" else "runtime")
            python_month = search(r".*-(\d{2})-.*", date)
            if not python_month:
                continue
            month = "{:02}".format((int(python_month.group(1)) - 1) % 12)
            start = [
                int(i)
                for i in sub(
                    r"(\d+)-(\d+)-(\d+) (\d+):(\d+).*",
                    r"\1," + month + r",\3,\4,\5",
                    date,
                ).split(",")
            ]
            instance_properties = instance.get_properties(include=properties)
            results[instance.name] = {"start": start, **instance_properties}
        return results

    def clear_results(self, service_id):
        for result in db.fetch(
            "run", all_matches=True, allow_none=True, service_id=service_id
        ):
            db.session.delete(result)

    def compare(self, type, id, v1, v2, context_lines):
        if type in ("result", "device_result"):
            first = vs.dict_to_string(getattr(db.fetch("result", id=v1), "result"))
            second = vs.dict_to_string(getattr(db.fetch("result", id=v2), "result"))
        else:
            device = db.fetch("device", id=id)
            result1 = self.get_git_network_data(device.name, v1)
            result2 = self.get_git_network_data(device.name, v2)
            v1, v2 = result1["datetime"], result2["datetime"]
            first, second = result1["result"][type], result2["result"][type]
        return "\n".join(
            unified_diff(
                first.splitlines(),
                second.splitlines(),
                fromfile=f"V1 ({v1})",
                tofile=f"V2 ({v2})",
                lineterm="",
                n=int(context_lines),
            )
        )

    def copy_service_in_workflow(self, workflow_id, **kwargs):
        service_sets = list(set(kwargs["services"].split(",")))
        service_instances = db.objectify("service", service_sets)
        workflow = db.fetch("workflow", id=workflow_id, rbac="edit")
        services, errors, shallow_copy = [], [], kwargs["mode"] == "shallow"
        for service in service_instances:
            if shallow_copy and not service.shared:
                errors.append(f"'{service.name}' is not a shared service.")
            elif shallow_copy and service in workflow.services:
                errors.append(f"This workflow already contains '{service.name}'.")
            elif service.scoped_name == "Placeholder" and not shallow_copy:
                errors.append("Deep Copy cannot be used for the placeholder service.")
        if errors:
            return {"alert": errors}
        for service in service_instances:
            if kwargs["mode"] == "deep":
                service = service.duplicate(workflow)
            else:
                workflow.services.append(service)
            services.append(service)
        workflow.update_last_modified_properties()
        db.session.commit()
        return {
            "services": [service.serialized for service in services],
            "update_time": workflow.last_modified,
        }

    def count_models(self):
        active_service, active_workflow = 0, 0
        for run in db.fetch_all("run", rbac=None, status="Running"):
            active_service += 1
            active_workflow += run.service.type == "workflow"
        return {
            "counters": {
                model: db.query(model, rbac=None)
                .with_entities(vs.models[model].id)
                .count()
                for model in vs.properties["dashboard"]
            },
            "active": {
                "service": active_service,
                "task": len(db.fetch_all("task", rbac=None, is_active=True)),
                "workflow": active_workflow,
            },
            "properties": {
                model: self.counters(vs.properties["dashboard"][model][0], model)
                for model in vs.properties["dashboard"]
            },
        }

    def counters(self, property, model):
        return Counter(v for v, in db.query(model, properties=[property], rbac=None))

    def create_label(self, type, id, x, y, label_id, **kwargs):
        workflow = db.fetch(type, id=id, rbac="edit")
        label_id = str(uuid4()) if label_id == "undefined" else label_id
        label = {
            "positions": [x, y],
            "content": kwargs["text"],
            "alignment": kwargs["alignment"],
            "size": kwargs["size"],
        }
        workflow.labels[label_id] = label
        return {"id": label_id, **label}

    def database_deletion(self, **kwargs):
        db.delete_all(*kwargs["deletion_types"])

    def delete_instance(self, model, instance_id):
        try:
            return db.delete(model, id=instance_id).get("name", "")
        except Exception as exc:
            return {"alert": f"Unable to delete {model} ({exc})"}

    def delete_builder_selection(self, type, id, **selection):
        instance = db.fetch(type, id=id)
        instance.update_last_modified_properties()
        instance.check_restriction_to_owners("edit")
        for edge_id in selection["edges"]:
            if type == "workflow":
                db.delete("workflow_edge", id=edge_id)
            else:
                instance.links.remove(db.fetch("link", id=edge_id))
        for node_id in selection["nodes"]:
            if isinstance(node_id, str):
                instance.labels.pop(node_id)
            elif type == "network":
                instance.nodes.remove(db.fetch("node", id=node_id))
            else:
                service = db.fetch("service", id=node_id)
                if not service.shared:
                    db.delete_instance(service)
                else:
                    instance.services.remove(service)
        return instance.last_modified

    def edit_file(self, filepath):
        try:
            with open(Path(filepath.replace(">", "/"))) as file:
                return file.read()
        except FileNotFoundError:
            file = db.fetch("file", path=filepath.replace(">", "/"), allow_none=True)
            if file:
                file.status = "Not Found"
            return {"error": "File not found on disk."}
        except UnicodeDecodeError:
            return {"error": "Cannot read file (unsupported type)."}

    def export_service(self, service_id):
        service = db.fetch("service", id=service_id)
        path = Path(vs.path / "files" / "services" / service.filename)
        path.mkdir(parents=True, exist_ok=True)
        services = (
            set(service.deep_services) if service.type == "workflow" else [service]
        )
        exclude = ("target_devices", "target_pools", "pools", "events")
        services = [
            service.to_dict(export=True, private_properties=True, exclude=exclude)
            for service in services
        ]
        with open(path / "service.yaml", "w") as file:
            yaml.dump(services, file)
        if service.type == "workflow":
            edges = [edge.to_dict(export=True) for edge in service.deep_edges]
            with open(path / "workflow_edge.yaml", "w") as file:
                yaml.dump(edges, file)
        with open_tar(f"{path}.tgz", "w:gz") as tar:
            tar.add(path, arcname=service.filename)
        rmtree(path, ignore_errors=True)
        return path

    def export_services(self, **kwargs):
        if kwargs["parent-filtering"] == "true":
            kwargs["workflows_filter"] = "empty"
        for service in self.filtering("service", properties=["id"], form=kwargs):
            self.export_service(service.id)

    def filtering_base_constraints(self, model, **kwargs):
        table, constraints = vs.models[model], []
        constraint_dict = {**kwargs.get("form", {}), **kwargs.get("constraints", {})}
        for property in vs.model_properties[model]:
            value, row = constraint_dict.get(property), getattr(table, property)
            filter_value = constraint_dict.get(f"{property}_filter")
            if not value and filter_value != "empty":
                continue
            if value in ("bool-true", "bool-false"):
                constraint = row == (value == "bool-true")
            elif filter_value == "equality":
                constraint = row == value
            elif filter_value == "empty":
                constraint = row == ""
            elif not filter_value or filter_value == "inclusion":
                constraint = row.contains(value, autoescape=isinstance(value, str))
            else:
                constraint = cast(row, String()).regexp_match(value)
            if constraint_dict.get(f"{property}_invert"):
                constraint = ~constraint
            constraints.append(constraint)
        return constraints

    def filtering_relationship_constraints(self, query, model, **kwargs):
        table = vs.models[model]
        constraint_dict = {**kwargs.get("form", {}), **kwargs.get("constraints", {})}
        for related_model, relation_properties in vs.relationships[model].items():
            related_table = aliased(vs.models[relation_properties["model"]])
            match = constraint_dict.get(f"{related_model}_filter")
            if match == "empty":
                query = query.filter(~getattr(table, related_model).any())
            else:
                relation_names = constraint_dict.get(related_model, [])
                if not relation_names:
                    continue
                if match == "union":
                    query = (
                        query.join(related_table, getattr(table, related_model))
                        .filter(related_table.name.in_(relation_names))
                        .group_by(table.id)
                    )
                else:
                    for name in relation_names:
                        new_table = aliased(vs.models[relation_properties["model"]])
                        query = query.join(
                            new_table, getattr(table, related_model)
                        ).filter(new_table.name == name)
        if constraint_dict.get("intersect"):
            intersect_model = constraint_dict["intersect"]["type"]
            intersect_table = aliased(vs.models[intersect_model])
            query = query.join(
                intersect_table, getattr(table, f"{intersect_model}s")
            ).filter(intersect_table.id == constraint_dict["intersect"]["id"])
        return query

    def filtering(
        self, model, bulk=False, rbac="read", username=None, properties=None, **kwargs
    ):
        table, pagination = vs.models[model], kwargs.get("pagination")
        query = db.query(model, rbac, username, properties=properties)
        total_records, filtered_records = (10**6,) * 2
        if pagination and not bulk and not properties:
            total_records = query.with_entities(table.id).count()
        constraints = self.filtering_base_constraints(model, **kwargs)
        constraints.extend(table.filtering_constraints(**kwargs))
        query = self.filtering_relationship_constraints(query, model, **kwargs)
        query = query.filter(and_(*constraints))
        if bulk or properties:
            instances = query.all()
            if bulk == "object" or properties:
                return instances
            else:
                return [getattr(instance, bulk) for instance in instances]
        if pagination:
            filtered_records = query.with_entities(table.id).count()
        data = kwargs["columns"][int(kwargs["order"][0]["column"])]["data"]
        ordering = getattr(getattr(table, data, None), kwargs["order"][0]["dir"], None)
        if ordering:
            query = query.order_by(ordering())
        try:
            query_data = (
                query.limit(int(kwargs["length"])).offset(int(kwargs["start"])).all()
            )
        except OperationalError:
            return {"error": "Invalid regular expression as search parameter."}
        table_result = {
            "draw": int(kwargs["draw"]),
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": [obj.table_properties(**kwargs) for obj in query_data],
        }
        if kwargs.get("export"):
            table_result["full_result"] = [
                obj.table_properties(**kwargs) for obj in query.all()
            ]
        if kwargs.get("clipboard"):
            table_result["full_result"] = ",".join(obj.name for obj in query.all())
        return table_result

    def get(self, model, id, **kwargs):
        if not kwargs:
            kwargs = vs.properties["serialized"]["get"].get(model, {})
        func = "get_properties" if kwargs.pop("properties_only", None) else "to_dict"
        return getattr(db.fetch(model, id=id), func)(**kwargs)

    def get_cluster_status(self):
        return [server.status for server in db.fetch_all("server")]

    def get_credentials(self, device, optional=False, **kwargs):
        if kwargs["credentials"] == "device":
            credentials = db.get_credential(
                current_user.name, device=device, optional=optional
            )
            if not credentials:
                return
            return credentials.username, env.get_password(credentials.password)
        elif kwargs["credentials"] == "user":
            return current_user.name, env.get_password(current_user.password)
        else:
            return kwargs["username"], kwargs["password"]

    def get_device_logs(self, device_id):
        device_logs = [
            log.name
            for log in db.fetch_all("log")
            if log.source == db.fetch("device", id=device_id).ip_address
        ]
        return "\n".join(device_logs)

    def get_device_network_data(self, device_id):
        device = db.fetch("device", id=device_id, rbac="configuration")
        return {
            property: vs.custom.parse_configuration_property(device, property)
            for property in vs.configuration_properties
        }

    def get_form_properties(self, service_id):
        form_factory.register_parameterized_form(service_id)
        return vs.form_properties[f"initial-{service_id}"]

    def get_git_content(self):
        env.log("info", "Starting Git Content Update")
        repo = vs.settings["app"]["git_repository"]
        if not repo:
            return
        local_path = vs.path / "network_data"
        try:
            if exists(local_path):
                Repo(local_path).remotes.origin.pull()
            else:
                local_path.mkdir(parents=True, exist_ok=True)
                Repo.clone_from(repo, local_path)
        except Exception as exc:
            env.log("error", f"Git pull failed ({str(exc)})")
        try:
            self.update_database_configurations_from_git()
        except Exception as exc:
            env.log("error", f"Update of device configurations failed ({str(exc)})")
        env.log("info", "Git Content Update Successful")

    def get_git_history(self, device_id):
        device = db.fetch("device", id=device_id, rbac="configuration")
        repo = Repo(vs.path / "network_data")
        path = vs.path / "network_data" / device.name
        return {
            data_type: [
                {"hash": str(commit), "date": commit.committed_datetime}
                for commit in list(repo.iter_commits(paths=path / data_type))
            ]
            for data_type in vs.configuration_properties
        }

    def get_git_network_data(self, device_name, hash):
        commit, result = Repo(vs.path / "network_data").commit(hash), {}
        device = db.fetch("device", name=device_name, rbac="configuration")
        for property in vs.configuration_properties:
            try:
                file = commit.tree / device_name / property
                with BytesIO(file.data_stream.read()) as f:
                    value = f.read().decode("utf-8")
                result[property] = vs.custom.parse_configuration_property(
                    device, property, value
                )
            except KeyError:
                result[property] = ""
        return {"result": result, "datetime": commit.committed_datetime}

    def get_migration_folders(self):
        return listdir(vs.path / "files" / "migrations")

    def get_properties(self, model, id):
        return db.fetch(model, id=id).get_properties()

    def get_report(self, service_id, runtime):
        return getattr(
            db.fetch(
                "service_report",
                allow_none=True,
                runtime=runtime,
                service_id=service_id,
            ),
            "content",
            "",
        )

    def get_report_template(self, template):
        return vs.reports[template]

    def get_result(self, id):
        return db.fetch("result", id=id).result

    def get_runtimes(self, id, display=None):
        kwargs = {"allow_none": True, "all_matches": True, "service_id": id}
        if display == "user":
            kwargs["creator"] = current_user.name
        results, runs = db.fetch("result", **kwargs), db.fetch("run", **kwargs)
        results_runtimes = set((r.parent_runtime, r.run.name) for r in results)
        run_runtimes = set((run.runtime, run.name) for run in runs)
        return sorted(results_runtimes | run_runtimes, reverse=True)

    def get_service_logs(self, service, runtime, line=0, device=None):
        log_instance = db.fetch(
            "service_log", allow_none=True, runtime=runtime, service_id=service
        )
        number_of_lines = 0
        if log_instance:
            lines = log_instance.content.splitlines()
        else:
            lines = (
                env.log_queue(runtime, service, start_line=int(line), mode="get") or []
            )
            number_of_lines = len(lines)
        if device:
            device_name = db.fetch("device", id=device).name
            lines = [line for line in lines if f"DEVICE {device_name}" in line]
        return {
            "logs": "\n".join(lines),
            "refresh": not log_instance,
            "line": int(line) + number_of_lines,
        }

    def get_service_state(self, path, **kwargs):
        state, run, path_id = None, None, path.split(">")
        runtime, display = kwargs.get("runtime"), kwargs.get("display")
        output = {"runtime": runtime}
        service = db.fetch("service", id=path_id[-1], allow_none=True)
        if not service:
            raise db.rbac_error
        runs = db.query("run", rbac=None).filter(
            vs.models["run"].service_id.in_(path_id)
        )
        if display == "user":
            runs = runs.filter(vs.models["run"].creator == current_user.name)
        runs = runs.all()
        if runtime != "normal" and runs:
            if runtime == "latest":
                run = sorted(runs, key=attrgetter("runtime"), reverse=True)[0]
            else:
                run = db.fetch("run", allow_none=True, runtime=runtime)
            state = run.get_state() if run else None
        if kwargs.get("device") and run:
            output["device_state"] = {
                result.service_id: result.success
                for result in db.fetch_all(
                    "result", parent_runtime=run.runtime, device_id=kwargs.get("device")
                )
            }
        serialized_service = service.to_dict(include=["edges", "superworkflow"])
        run_properties = vs.automation["workflow"]["state_properties"]["run"]
        service_properties = vs.automation["workflow"]["state_properties"]["service"]
        if service.type == "workflow":
            serialized_service["services"] = []
            for subservice in service.services:
                properties = subservice.get_properties(include=service_properties)
                subservice_positions = subservice.positions.get(service.name, [0, 0])
                properties["x"], properties["y"] = subservice_positions
                serialized_service["services"].append(properties)
        return {
            "service": serialized_service,
            "runtimes": sorted(
                set((run.runtime, run.name) for run in runs), reverse=True
            ),
            "state": state,
            "run": run.get_properties(include=run_properties) if run else None,
            **output,
        }

    def get_session_log(self, session_id):
        return db.fetch("session", id=session_id).content

    def get_network_state(self, path, runtime=None):
        network = db.fetch("network", id=path.split(">")[-1], allow_none=True)
        if not network:
            raise db.rbac_error
        return {
            "network": network.to_dict(include=["nodes", "links"]),
            "device_results": {
                result.device_id: result.success
                for result in db.fetch_all("result", parent_runtime=runtime)
                if result.device_id
            },
        }

    def get_top_level_instances(self, type):
        result = defaultdict(list)
        constraints = [~getattr(vs.models[type], f"{type}s").any()]
        if type == "workflow":
            constraints.append(vs.models[type].shared == true())
        for instance in (
            db.query(type, properties=["id", "category", "name"])
            .filter(or_(*constraints))
            .all()
        ):
            result[instance.category or "Other"].append(dict(instance))
        return result

    def scan_folder(self, path=None):
        env.log("info", "Starting Scan of Files")
        path = env.file_path if not path else path.replace(">", "/")
        folders = {Path(path)}
        while folders:
            folder = folders.pop()
            for file in folder.iterdir():
                if file.suffix in vs.settings["files"]["ignored_types"]:
                    continue
                if file.is_dir():
                    folders.add(file)
                if db.fetch("file", path=str(file), allow_none=True):
                    continue
                db.factory("folder" if file.is_dir() else "file", path=str(file))
            db.session.commit()
        env.log("info", "Scan of Files Successful")

    def get_visualization_pools(self, view):
        has_device = vs.models["pool"].devices.any()
        has_link = vs.models["pool"].links.any()
        pools = db.query("pool").filter(or_(has_device, has_link)).all()
        return [pool.base_properties for pool in pools]

    def get_workflow_results(self, path, runtime):
        run = db.fetch("run", runtime=runtime)
        service = db.fetch("service", id=path.split(">")[-1])
        state = run.state

        def rec(service, path):
            results = db.fetch(
                "result",
                parent_runtime=runtime,
                allow_none=True,
                all_matches=True,
                service_id=service.id,
            )
            if service.scoped_name in ("Start", "End") or not results:
                return
            progress = state.get(path, {}).get("progress")
            track_progress = progress and progress["device"]["total"]
            data = {"progress": progress["device"]} if track_progress else {}
            success = all(result.success for result in results)
            color = "32CD32" if success else "FF6666"
            result = {
                "runtime": min(result.runtime for result in results),
                "data": {"properties": service.base_properties, **data},
                "text": service.scoped_name,
                "a_attr": {"style": f"color: #{color};width: 100%"},
            }
            if service.type == "workflow":
                children_results = []
                for child in service.services:
                    if child.scoped_name == "Placeholder":
                        child = run.placeholder
                    child_results = rec(child, f"{path}>{child.id}")
                    if not child_results:
                        continue
                    children_results.append(child_results)
                return {
                    "children": sorted(children_results, key=itemgetter("runtime")),
                    **result,
                }
            else:
                return result

        return rec(service, path)

    def get_workflow_services(self, id, node):
        parents = db.fetch("workflow", id=id).get_ancestors()
        if node == "all":
            workflows = self.filtering(
                "workflow", bulk="object", constraints={"workflows_filter": "empty"}
            )
            return (
                [
                    {
                        "data": {"id": "standalone"},
                        "id": "standalone",
                        "text": "Standalone services",
                        "children": True,
                        "state": {"disabled": True},
                        "a_attr": {
                            "class": "no_checkbox",
                            "style": "color: #000000; width: 100%",
                        },
                        "type": "category",
                    }
                ]
                + [
                    {
                        "data": {"id": "shared"},
                        "id": "shared",
                        "text": "Shared services",
                        "children": True,
                        "state": {"disabled": True},
                        "a_attr": {
                            "class": "no_checkbox",
                            "style": "color: #FF1694; width: 100%",
                        },
                        "type": "category",
                    }
                ]
                + sorted(
                    (
                        {
                            "id": workflow.name,
                            "data": {"id": workflow.id},
                            "text": workflow.name,
                            "children": True,
                            "type": "workflow",
                            "state": {"disabled": workflow in parents},
                            "a_attr": {
                                "class": "no_checkbox" if workflow in parents else "",
                                "style": "color: #6666FF; width: 100%",
                            },
                        }
                        for workflow in workflows
                    ),
                    key=itemgetter("text"),
                )
            )
        elif node == "standalone":
            constraints = {"workflows_filter": "empty", "type": "service"}
            services = self.filtering("service", bulk="object", constraints=constraints)
            return sorted(
                (
                    {
                        "data": {"id": service.id},
                        "text": service.scoped_name,
                        "a_attr": {"style": ("color: #6666FF;" "width: 100%")},
                    }
                    for service in services
                ),
                key=itemgetter("text"),
            )
        elif node == "shared":
            constraints = {"shared": "bool-true"}
            services = self.filtering("service", bulk="object", constraints=constraints)
            return sorted(
                (
                    {
                        "data": {"id": service.id},
                        "text": service.scoped_name,
                        "a_attr": {"style": ("color: #FF1694;" "width: 100%")},
                    }
                    for service in services
                    if service.scoped_name not in ("Start", "End")
                ),
                key=itemgetter("text"),
            )
        else:
            return sorted(
                (
                    {
                        "data": {"id": service.id},
                        "text": service.scoped_name,
                        "children": service.type == "workflow",
                        "type": "workflow" if service.type == "workflow" else "service",
                        "state": {"disabled": service in parents},
                        "a_attr": {
                            "class": "no_checkbox" if service in parents else "",
                            "style": (
                                f"color: #{'FF1694' if service.shared else '6666FF'};"
                                "width: 100%"
                            ),
                        },
                    }
                    for service in db.fetch("workflow", id=node).services
                    if service.scoped_name not in ("Start", "End")
                ),
                key=itemgetter("text"),
            )

    def get_instance_tree(self, type, full_path):
        path_id = full_path.split(">")

        def rec(instance, path=""):
            path += ">" * bool(path) + str(instance.id)
            if type == "workflow":
                if instance.scoped_name in ("Start", "End"):
                    return
                elif instance.scoped_name == "Placeholder" and len(path_id) > 1:
                    instance = db.fetch(type, id=path_id[1])
            child_property = "nodes" if type == "network" else "services"
            color = "FF1694" if getattr(instance, "shared", False) else "6666FF"
            return {
                "data": {"path": path, **instance.base_properties},
                "id": instance.id,
                "state": {"opened": full_path.startswith(path)},
                "text": instance.scoped_name if type == "workflow" else instance.name,
                "children": sorted(
                    filter(
                        None,
                        [
                            rec(child, path)
                            for child in getattr(instance, child_property)
                        ],
                    ),
                    key=lambda node: node["text"].lower(),
                )
                if instance.type == type
                else False,
                "a_attr": {
                    "class": "no_checkbox",
                    "style": f"color: #{color}; width: 100%",
                },
                "type": instance.type,
            }

        return rec(db.fetch(type, id=path_id[0]))

    def load_debug_snippets(self):
        snippets = {}
        for path in Path(vs.path / "files" / "snippets").glob("**/*.py"):
            with open(path, "r") as file:
                snippets[path.name] = file.read()
        return snippets

    def migration_export(self, **kwargs):
        for cls_name in kwargs["import_export_types"]:
            path = vs.path / "files" / "migrations" / kwargs["name"]
            if not exists(path):
                makedirs(path)
            with open(path / f"{cls_name}.yaml", "w") as migration_file:
                yaml.dump(
                    db.export(
                        cls_name,
                        private_properties=kwargs["export_private_properties"],
                    ),
                    migration_file,
                )

    def migration_import(self, folder="migrations", **kwargs):
        env.log("info", "Starting Migration Import")
        status, models = "Import successful.", kwargs["import_export_types"]
        empty_database = kwargs.get("empty_database_before_import", False)
        if empty_database:
            db.delete_all(*models)
        fetch_instance = {
            "user": [current_user.name] if current_user else [],
            "service": ["[Shared] Start", "[Shared] End", "[Shared] Placeholder"],
        }
        relations = defaultdict(lambda: defaultdict(dict))
        service_instances = []
        for model in models:
            path = vs.path / "files" / folder / kwargs["name"] / f"{model}.yaml"
            if not path.exists():
                if kwargs.get("service_import") and model == "service":
                    raise Exception("Invalid archive provided in service import.")
                continue
            with open(path, "r") as migration_file:
                instances = yaml.load(migration_file)
                for instance in instances:
                    type, relation_dict = instance.pop("type", model), {}
                    for related_model, relation in vs.relationships[type].items():
                        relation_dict[related_model] = instance.pop(related_model, [])
                    instance_private_properties = {
                        property: env.get_password(instance.pop(property))
                        for property in list(instance)
                        if property in vs.private_properties_set
                    }
                    try:
                        existing_instance = instance["name"] in fetch_instance.get(
                            model, []
                        )
                        instance = db.factory(
                            type,
                            migration_import=True,
                            no_fetch=empty_database and not existing_instance,
                            update_pools=False,
                            import_mechanism=True,
                            **instance,
                        )
                        if kwargs.get("service_import"):
                            if instance.type == "workflow":
                                instance.edges = []
                            if model == "service":
                                service_instances.append(instance)
                        relations[type][instance.name] = relation_dict
                        for property in instance_private_properties.items():
                            setattr(instance, *property)
                    except Exception:
                        info(f"{str(instance)} could not be imported:\n{format_exc()}")
                        if kwargs.get("service_import", False):
                            db.session.rollback()
                            return "Error during import; service was not imported."
                        status = "Partial import (see logs)."
            db.session.commit()
        for model, instances in relations.items():
            for instance_name, related_models in instances.items():
                for property, value in related_models.items():
                    if not value:
                        continue
                    relation = vs.relationships[model][property]
                    if relation["list"]:
                        related_instances = (
                            db.fetch(relation["model"], name=name, allow_none=True)
                            for name in value
                        )
                        value = list(filter(None, related_instances))
                    else:
                        value = db.fetch(relation["model"], name=value, allow_none=True)
                    try:
                        setattr(db.fetch(model, name=instance_name), property, value)
                    except Exception:
                        info("\n".join(format_exc().splitlines()))
                        if kwargs.get("service_import", False):
                            db.session.rollback()
                            return "Error during import; service was not imported."
                        status = "Partial import (see logs)."
        db.session.commit()
        if kwargs.get("service_import", False):
            main_workflow = [
                service for service in service_instances if not service.workflows
            ][0]
            main_workflow.recursive_update()
        if not kwargs.get("skip_model_update"):
            for model in ("user", "service", "network"):
                for instance in db.fetch_all(model):
                    instance.post_update()
        if not kwargs.get("skip_pool_update"):
            for pool in db.fetch_all("pool"):
                pool.compute_pool()
        db.session.commit()
        env.log("info", status)
        return status

    def multiselect_filtering(self, model, **params):
        table = vs.models[model]
        query = db.query(model).filter(table.name.contains(params.get("term")))
        query = self.filtering_relationship_constraints(query, model, **params)
        query = query.filter(and_(*self.filtering_base_constraints(model, **params)))
        property = "name" if params["multiple"] else "id"
        button_html = "type='button' class='btn btn-link btn-select2'"
        return {
            "items": [
                {
                    "text": f"<button {button_html}>{result.ui_name}</button>",
                    "id": getattr(result, property),
                }
                for result in query.limit(10)
                .offset((int(params["page"]) - 1) * 10)
                .all()
            ],
            "total_count": query.count(),
        }

    def import_services(self, **kwargs):
        file = kwargs["file"]
        filepath = vs.path / "files" / "services" / file.filename
        file.save(str(filepath))
        with open_tar(filepath) as tar_file:
            tar_file.extractall(path=vs.path / "files" / "services")
            folder_name = tar_file.getmembers()[0].name
            status = self.migration_import(
                folder="services",
                name=folder_name,
                import_export_types=["service", "workflow_edge"],
                service_import=True,
                skip_pool_update=True,
                skip_model_update=True,
            )
        rmtree(vs.path / "files" / "services" / folder_name, ignore_errors=True)
        if "Error during import" in status:
            raise Exception(status)
        return status

    def import_topology(self, **kwargs):
        file = kwargs["file"]
        if kwargs["replace"]:
            db.delete_all("device")
        result = self.topology_import(file)
        info("Inventory import: Done.")
        return result

    def objectify(self, model, instance):
        for property, relation in vs.relationships[model].items():
            if property not in instance:
                continue
            elif relation["list"]:
                instance[property] = [
                    db.fetch(relation["model"], name=name).id
                    for name in instance[property]
                ]
            else:
                instance[property] = db.fetch(
                    relation["model"], name=instance[property]
                ).id
        return instance

    def remove_instance(self, **kwargs):
        instance = db.fetch(kwargs["instance"]["type"], id=kwargs["instance"]["id"])
        target = db.fetch(kwargs["relation"]["type"], id=kwargs["relation"]["id"])
        if target.type == "pool" and not target.manually_defined:
            return {"alert": "Removing an object from a dynamic pool is an allowed."}
        relationship_property = getattr(target, kwargs["relation"]["relation"]["to"])
        if instance in relationship_property:
            relationship_property.remove(instance)
        else:
            return {"alert": f"{instance.name} is not associated with {target.name}."}

    def result_log_deletion(self, **kwargs):
        date_time_object = datetime.strptime(kwargs["date_time"], "%d/%m/%Y %H:%M:%S")
        date_time_string = date_time_object.strftime("%Y-%m-%d %H:%M:%S.%f")
        for model in kwargs["deletion_types"]:
            if model == "run":
                field_name = "runtime"
            elif model == "changelog":
                field_name = "time"
            session_query = db.session.query(vs.models[model]).filter(
                getattr(vs.models[model], field_name) < date_time_string
            )
            session_query.delete(synchronize_session=False)
            db.session.commit()

    @staticmethod
    @actor(max_retries=0, time_limit=float("inf"))
    def run(service, **kwargs):
        current_thread().name = kwargs["runtime"]
        if "path" not in kwargs:
            kwargs["path"] = str(service)
        keys = list(vs.model_properties["run"]) + list(vs.relationships["run"])
        run_kwargs = {key: kwargs.pop(key) for key in keys if kwargs.get(key)}
        for property in ("name", "labels"):
            if property in kwargs.get("form", {}):
                run_kwargs[property] = kwargs["form"][property]
        service = db.fetch("service", id=service)
        service.status = "Running"
        initial_payload = {
            **service.initial_payload,
            **kwargs.get("form", {}).get("initial_payload", {}),
        }
        restart_runtime = kwargs.get("restart_runtime")
        restart_run = db.fetch("run", allow_none=True, runtime=restart_runtime)
        if service.type == "workflow" and service.superworkflow and not restart_run:
            run_kwargs["placeholder"] = run_kwargs["start_service"] = service.id
            run_kwargs["path"] = str(service.superworkflow.id)
            service = service.superworkflow
            initial_payload.update(service.initial_payload)
        else:
            run_kwargs["start_service"] = service.id
        if restart_run:
            run_kwargs["restart_run"] = restart_run
            initial_payload = restart_run.payload
        run_kwargs["services"] = [service.id]
        run = db.factory("run", service=service.id, commit=True, **run_kwargs)
        run.properties, run.payload = kwargs, {**initial_payload, **kwargs}
        return run.run()

    def run_debug_code(self, **kwargs):
        result = StringIO()
        with redirect_stdout(result):
            try:
                exec(
                    kwargs["code"],
                    {
                        "controller": self,
                        "env": env,
                        "db": db,
                        "models": vs.models,
                        "vs": vs,
                    },
                )
            except Exception:
                return format_exc()
        return result.getvalue()

    def run_service(self, path, **kwargs):
        if isinstance(kwargs.get("start_services"), str):
            kwargs["start_services"] = kwargs["start_services"].split("-")
        service_id = str(path).split(">")[-1]
        for property in ("user", "csrf_token"):
            kwargs.pop(property, None)
        if kwargs.get("form_type", "").startswith("initial-"):
            kwargs = {"form": kwargs, "parameterized_run": True}
        kwargs.update({"creator": getattr(current_user, "name", ""), "path": path})
        service = db.fetch("service", id=service_id, rbac="run")
        if service.disabled:
            return {"error": "The workflow is disabled."}
        service.check_restriction_to_owners("run")
        kwargs["runtime"] = runtime = vs.get_time()
        run_name = kwargs.get("form", {}).get("name")
        if run_name and db.fetch("run", name=run_name, allow_none=True):
            return {"error": "There is already a run with the same name."}
        if kwargs.get("asynchronous", True):
            if vs.settings["automation"]["use_task_queue"]:
                self.run.send(service_id, **kwargs)
            else:
                Thread(target=self.run, args=(service_id,), kwargs=kwargs).start()
        else:
            service.run(runtime=runtime)
        return {
            "service": service.serialized,
            "runtime": runtime,
            "restart": "restart_runtime" in kwargs,
            "user": current_user.name,
        }

    def run_service_on_targets(self, **kwargs):
        return self.run_service(
            kwargs["service"],
            **{f"target_{kwargs['type']}s": kwargs["targets"].split("-")},
        )

    def save_file(self, filepath, **kwargs):
        filepath, content = filepath.replace(">", "/"), None
        if kwargs.get("file_content"):
            with open(Path(filepath), "w") as file:
                content = file.write(kwargs["file_content"])
        db.fetch("file", path=filepath).update()
        return content

    def save_positions(self, type, id, **kwargs):
        now, old_position = vs.get_time(), None
        instance = db.fetch(type, allow_none=True, id=id, rbac="edit")
        if not instance:
            return
        relation_type = "node" if type == "network" else "service"
        for id, position in kwargs.items():
            new_position = [position["x"], position["y"]]
            if "-" not in id:
                relation = db.fetch(relation_type, id=id, rbac=None)
                old_position = relation.positions.get(instance.name)
                relation.positions[instance.name] = new_position
            elif id in instance.labels:
                old_position = instance.labels[id].pop("positions")
                instance.labels[id] = {"positions": new_position, **instance.labels[id]}
        return now

    def save_profile(self, **kwargs):
        allow_password_change = vs.settings["authentication"]["allow_password_change"]
        if not allow_password_change or current_user.authentication != "database":
            kwargs.pop("password", None)
        current_user.update(**kwargs)

    def save_settings(self, **kwargs):
        vs.settings = vs.template_context["settings"] = kwargs["settings"]
        if kwargs["save"]:
            with open(vs.path / "setup" / "settings.json", "w") as file:
                dump(kwargs["settings"], file, indent=2)

    def scan_cluster(self, **kwargs):
        protocol = vs.settings["cluster"]["scan_protocol"]
        for ip_address in IPv4Network(vs.settings["cluster"]["scan_subnet"]):
            try:
                server = http_get(
                    f"{protocol}://{ip_address}/rest/is_alive",
                    timeout=vs.settings["cluster"]["scan_timeout"],
                ).json()
                if vs.settings["cluster"]["id"] != server.pop("cluster_id"):
                    continue
                db.factory("server", **{**server, **{"ip_address": str(ip_address)}})
            except ConnectionError:
                continue

    def scan_playbook_folder(self):
        path = vs.settings["paths"]["playbooks"] or vs.path / "files" / "playbooks"
        playbooks = [
            [str(file) for file in Path(path).glob(extension)]
            for extension in ("*.yaml", "*.yml")
        ]
        return sorted(sum(playbooks, []))

    def scheduler_action(self, mode, **kwargs):
        for task in self.filtering("task", properties=["id"], form=kwargs):
            self.task_action(mode, task.id)

    def search_builder(self, type, id, text):
        property = "nodes" if type == "network" else "services"
        return [
            node.id
            for node in getattr(db.fetch(type, id=id), property)
            if text.lower() in str(node.get_properties().values()).lower()
        ]

    def search_workflow_services(self, **kwargs):
        service_alias = aliased(vs.models["service"])
        workflows = [
            workflow.name
            for workflow in db.query("workflow", properties=["name"])
            .join(service_alias, vs.models["workflow"].services)
            .filter(service_alias.scoped_name.contains(kwargs["str"].lower()))
            .distinct()
            .all()
        ]
        return ["standalone", "shared", *workflows]

    def skip_services(self, workflow_id, service_ids):
        services = [db.fetch("service", id=id) for id in service_ids.split("-")]
        workflow = db.fetch("workflow", id=workflow_id, rbac="edit")
        skip = not all(service.skip.get(workflow.name) for service in services)
        for service in services:
            service.skip[workflow.name] = skip
        workflow.update_last_modified_properties()
        return {
            "skip": "skip" if skip else "unskip",
            "update_time": workflow.last_modified,
        }

    def stop_run(self, runtime):
        run = db.fetch("run", allow_none=True, runtime=runtime)
        if run and run.status == "Running":
            if env.redis_queue:
                env.redis("set", f"stop/{runtime}", "true")
            else:
                vs.run_stop[runtime] = True
            return True

    def switch_menu(self, user_id):
        user = db.fetch("user", rbac=None, id=user_id)
        user.small_menu = not user.small_menu

    def switch_theme(self, user_id, theme):
        db.fetch("user", rbac=None, id=user_id).theme = theme

    def task_action(self, mode, task_id):
        return db.fetch("task", id=task_id, rbac="edit").schedule(mode)

    def topology_export(self, **kwargs):
        workbook = Workbook()
        filename = kwargs["export_filename"]
        if "." not in filename:
            filename += ".xls"
        for obj_type in ("device", "link"):
            sheet = workbook.add_sheet(obj_type)
            for index, property in enumerate(vs.model_properties[obj_type]):
                if property in db.dont_migrate[obj_type]:
                    continue
                sheet.write(0, index, property)
                for obj_index, obj in enumerate(db.fetch_all(obj_type), 1):
                    value = getattr(obj, property)
                    if type(value) == bytes:
                        value = str(env.decrypt(value), "utf-8")
                    sheet.write(obj_index, index, str(value))
        workbook.save(vs.path / "files" / "spreadsheets" / filename)

    def topology_import(self, file):
        book = open_workbook(file_contents=file.read())
        status = "Topology successfully imported."
        for obj_type in ("device", "link"):
            try:
                sheet = book.sheet_by_name(obj_type)
            except XLRDError:
                continue
            properties = sheet.row_values(0)
            for row_index in range(1, sheet.nrows):
                values = {}
                for index, property in enumerate(properties):
                    if not property:
                        continue
                    property_type = vs.model_properties[obj_type].get(property, "str")
                    func = db.field_conversion[property_type]
                    values[property] = func(sheet.row_values(row_index)[index])
                try:
                    db.factory(obj_type, **values).serialized
                except Exception as exc:
                    info(f"{str(values)} could not be imported ({str(exc)})")
                    status = "Partial import (see logs)."
            db.session.commit()
        for pool in db.fetch_all("pool"):
            pool.compute_pool()
        env.log("info", status)
        return status

    def update(self, type, **kwargs):
        try:
            kwargs.update(
                {
                    "update_pools": True,
                    "must_be_new": kwargs.get("id") == "",
                }
            )
            for arg in ("name", "scoped_name"):
                if arg in kwargs:
                    kwargs[arg] = kwargs[arg].strip()
            if kwargs["must_be_new"]:
                kwargs["creator"] = kwargs["user"] = getattr(current_user, "name", "")
                for builder_type in ("workflow", "network"):
                    if not kwargs.get(f"{builder_type}s"):
                        continue
                    builder_id = kwargs[f"{builder_type}s"][0]
                    db.fetch(builder_type, id=builder_id, rbac="edit")
            instance = db.factory(type, **kwargs)
            if kwargs.get("copy"):
                db.fetch(type, id=kwargs["copy"]).duplicate(clone=instance)
            db.session.flush()
            return instance.post_update()
        except db.rbac_error:
            return {"alert": "Error 403 - Not Authorized."}
        except Exception as exc:
            db.session.rollback()
            if isinstance(exc, IntegrityError):
                alert = (
                    f"There is already a {instance.class_type} "
                    "with the same parameters."
                )
                return {"alert": alert}
            env.log("error", format_exc())
            return {"alert": str(exc)}

    def update_all_pools(self):
        for pool in db.fetch_all("pool"):
            pool.compute_pool()

    def update_database_configurations_from_git(self):
        path = vs.path / "network_data"
        env.log("info", f"Updating device configurations with data from {path}")
        for dir in scandir(path):
            device = db.fetch("device", allow_none=True, name=dir.name)
            timestamp_path = Path(dir.path) / "timestamps.json"
            if not device:
                continue
            try:
                with open(timestamp_path) as file:
                    timestamps = load(file)
            except Exception:
                timestamps = {}
            for property in vs.configuration_properties:
                for timestamp, value in timestamps.get(property, {}).items():
                    setattr(device, f"last_{property}_{timestamp}", value)
                filepath = Path(dir.path) / property
                if not filepath.exists():
                    continue
                with open(filepath) as file:
                    setattr(device, property, file.read())
        db.session.commit()
        for pool in db.fetch_all("pool"):
            if any(
                getattr(pool, f"device_{property}")
                for property in vs.configuration_properties
            ):
                pool.compute_pool()
        db.session.commit()

    def update_device_rbac(self):
        for group in db.fetch_all("group"):
            for property in vs.rbac["rbac_models"]["device"]:
                pool_property = getattr(vs.models["pool"], f"rbac_group_{property}")
                devices = (
                    db.query("device")
                    .join(vs.models["device"].pools)
                    .join(vs.models["group"], pool_property)
                    .filter(vs.models["group"].id == group.id)
                    .all()
                )
                setattr(group, f"{property}_devices", devices)

    def upload_files(self, **kwargs):
        kwargs["file"].save(f"{kwargs['folder']}/{kwargs['file'].filename}")

    def update_pool(self, pool_id):
        db.fetch("pool", id=int(pool_id), rbac="edit").compute_pool()

    def view_filtering(self, **kwargs):
        return {
            f"{model}s": self.filtering(model, **form, bulk="view_properties")
            for model, form in kwargs.items()
        }

    def web_connection(self, device_id, **kwargs):
        if not vs.settings["ssh"]["credentials"][kwargs["credentials"]]:
            return {"alert": "Unauthorized authentication method."}
        device = db.fetch("device", id=device_id, rbac="connect")
        port, endpoint = env.get_ssh_port(), str(uuid4())
        command = f"{vs.settings['ssh']['command']} -p {port}"
        if vs.settings["ssh"]["bypass_key_prompt"]:
            options = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        else:
            options = ""
        environment = {
            **{key: str(value) for key, value in vs.settings["ssh"]["web"].items()},
            "APP_ADDRESS": getenv("SERVER_URL", "https://0.0.0.0"),
            "DEVICE": str(device.id),
            "ENDPOINT": endpoint,
            "ENMS_USER": getenv("ENMS_USER", "admin"),
            "ENMS_PASSWORD": getenv("ENMS_PASSWORD", "admin"),
            "FLASK_APP": "app.py",
            "IP_ADDRESS": getattr(device, kwargs["address"]),
            "OPTIONS": options,
            "PORT": str(device.port),
            "PROTOCOL": kwargs["protocol"],
            "REDIRECTION": str(vs.settings["ssh"]["port_redirection"]),
            "USER": current_user.name,
        }
        if "authentication" in kwargs:
            credentials = self.get_credentials(device, optional=True, **kwargs)
            if not credentials:
                return {"alert": f"No credentials found for '{device.name}'."}
            environment.update(zip(("USERNAME", "PASSWORD"), credentials))
        Popen(command, shell=True, cwd=vs.path / "terminal", env=environment)
        return {
            "device": device.name,
            "port": port,
            "endpoint": endpoint,
            "redirection": vs.settings["ssh"]["port_redirection"],
        }


controller = Controller()
