from collections import Counter, defaultdict
from contextlib import redirect_stdout
from datetime import datetime
from difflib import unified_diff
from flask_login import current_user
from git import Repo
from io import BytesIO, StringIO
from ipaddress import IPv4Network
from json import dump, load
from logging import info
from os import listdir, makedirs, remove, scandir
from os.path import exists, getmtime
from pathlib import Path
from re import compile, error as regex_error
from requests import get as http_get
from ruamel import yaml
from shutil import rmtree
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased
from tarfile import open as open_tar
from time import ctime
from traceback import format_exc
from uuid import uuid4
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

from eNMS import app
from eNMS.database import db
from eNMS.models import models, model_properties, property_types, relationships
from eNMS.setup import properties


class BaseController:
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
        target.last_modified = app.get_time()
        self.update_rbac(*instances)
        return {"number": len(instances), "target": target.base_properties}

    def add_objects_to_view(self, view_id, **kwargs):
        result = {"update_time": self.get_time()}
        for model in ("node", "line"):
            base_model = "device" if model == "node" else "link"
            result[f"{model}s"] = []
            for model_id in kwargs[f"{base_model}s"]:
                node = db.factory(model, device=model_id, view=view_id)
                result[f"{model}s"].append(node.serialized)
        return result

    def bulk_deletion(self, table, **kwargs):
        instances = self.filtering(table, bulk="id", form=kwargs)
        for instance_id in instances:
            db.delete(table, id=instance_id)
        return len(instances)

    def bulk_edit(self, table, **kwargs):
        instances = kwargs.pop("id").split("-")
        kwargs = {
            property: value
            for property, value in kwargs.items()
            if kwargs.get(f"bulk-edit-{property}")
        }
        for instance_id in instances:
            db.factory(table, id=instance_id, **kwargs)
        return len(instances)

    def bulk_removal(
        self,
        table,
        target_type,
        target_id,
        target_property,
        constraint_property,
        **kwargs,
    ):
        kwargs[constraint_property] = [target_id]
        target = db.fetch(target_type, id=target_id)
        if target.type == "pool" and not target.manually_defined:
            return {"alert": "Removing objects from a dynamic pool is an allowed."}
        instances = self.filtering(table, bulk="object", form=kwargs)
        for instance in instances:
            getattr(target, target_property).remove(instance)
        self.update_rbac(*instances)
        return len(instances)

    def compare(self, type, id, v1, v2, context_lines):
        if type in ("result", "device_result"):
            first = app.str_dict(getattr(db.fetch("result", id=v1), "result"))
            second = app.str_dict(getattr(db.fetch("result", id=v2), "result"))
        else:
            device = db.fetch("device", id=id)
            result1, v1 = self.get_git_network_data(device.name, v1)
            result2, v2 = self.get_git_network_data(device.name, v2)
            first, second = result1[type], result2[type]
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
        workflow = db.fetch("workflow", id=workflow_id)
        services, errors = [], []
        if kwargs["mode"] == "shallow":
            for service in service_instances:
                if not service.shared:
                    errors.append(f"'{service.name}' is not a shared service.")
                elif service in workflow.services:
                    errors.append(f"This workflow already contains '{service.name}'.")
        if errors:
            return {"alert": errors}
        for service in service_instances:
            if kwargs["mode"] == "deep":
                service = service.duplicate(workflow)
            else:
                workflow.services.append(service)
            services.append(service)
        workflow.last_modified = app.get_time()
        db.session.commit()
        return {
            "services": [service.serialized for service in services],
            "update_time": workflow.last_modified,
        }

    def count_models(self):
        return {
            "counters": {
                model: db.query(model, rbac=None)
                .with_entities(models[model].id)
                .count()
                for model in properties["dashboard"]
            },
            "properties": {
                model: self.counters(properties["dashboard"][model][0], model)
                for model in properties["dashboard"]
            },
        }

    def counters(self, property, model):
        return Counter(v for v, in db.query(model, property=property, rbac=None))

    def create_label(self, workflow_id, x, y, label_id, **kwargs):
        workflow = db.fetch("workflow", id=workflow_id, rbac="edit")
        label_id = str(uuid4()) if label_id == "undefined" else label_id
        label = {
            "positions": [x, y],
            "content": kwargs["text"],
            "alignment": kwargs["alignment"],
        }
        workflow.labels[label_id] = label
        return {"id": label_id, **label}

    def create_view_object(self, type, view_id, **kwargs):
        node = db.factory(type, view=view_id, **kwargs)
        db.session.flush()
        return {"time": self.get_time(), "node": node.serialized}

    def database_deletion(self, **kwargs):
        db.delete_all(*kwargs["deletion_types"])

    def delete_corrupted_edges(self):
        edges = set(db.fetch_all("workflow_edge"))
        duplicated_edges, number_of_corrupted_edges = defaultdict(list), 0
        for edge in list(edges):
            services = getattr(edge.workflow, "services", [])
            if (
                not edge.source
                or not edge.destination
                or not edge.workflow
                or edge.source not in services
                or edge.destination not in services
            ):
                edges.remove(edge)
                db.session.delete(edge)
                number_of_corrupted_edges += 1
        db.session.commit()
        for edge in edges:
            duplicated_edges[
                (
                    edge.source.name,
                    edge.destination.name,
                    edge.workflow.name,
                    edge.subtype,
                )
            ].append(edge)
        for duplicates in duplicated_edges.values():
            for duplicate in duplicates[1:]:
                db.session.delete(duplicate)
                number_of_corrupted_edges += 1
        return number_of_corrupted_edges

    def delete_file(self, filepath):
        remove(Path(filepath.replace(">", "/")))

    def delete_instance(self, model, instance_id):
        return db.delete(model, id=instance_id)

    def delete_view_selection(self, selection):
        for instance_id in selection:
            db.delete("view_object", id=instance_id)
        return self.get_time()

    def delete_workflow_selection(self, workflow_id, **selection):
        workflow = db.fetch("workflow", id=workflow_id)
        workflow.last_modified = app.get_time()
        for edge_id in selection["edges"]:
            db.delete("workflow_edge", id=edge_id)
        for node_id in selection["nodes"]:
            if isinstance(node_id, str):
                workflow.labels.pop(node_id)
            else:
                service = db.fetch("service", id=node_id)
                workflow.services.remove(service)
                if not service.shared:
                    db.delete("service", id=service.id)
        return workflow.last_modified

    def duplicate_workflow(self, workflow_id):
        workflow = db.fetch("workflow", id=workflow_id)
        return workflow.duplicate().serialized

    def edit_file(self, filepath):
        try:
            with open(Path(filepath.replace(">", "/"))) as file:
                return file.read()
        except UnicodeDecodeError:
            return {"error": "Cannot read file (unsupported type)."}

    def export_service(self, service_id):
        service = db.fetch("service", id=service_id)
        path = Path(app.path / "files" / "services" / service.filename)
        path.mkdir(parents=True, exist_ok=True)
        services = service.deep_services if service.type == "workflow" else [service]
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

    def filtering_base_constraints(self, model, **kwargs):
        table, constraints = models[model], []
        constraint_dict = {**kwargs.get("form", {}), **kwargs.get("constraints", {})}
        for property in model_properties[model]:
            value, row = constraint_dict.get(property), getattr(table, property)
            if not value:
                continue
            filter_value = constraint_dict.get(f"{property}_filter")
            if value in ("bool-true", "bool-false"):
                constraint = row == (value == "bool-true")
            elif filter_value == "equality":
                constraint = row == value
            elif not filter_value or filter_value == "inclusion":
                constraint = row.contains(value, autoescape=isinstance(value, str))
            else:
                compile(value)
                regex_operator = "~" if db.dialect == "postgresql" else "regexp"
                constraint = row.op(regex_operator)(value)
            if constraint_dict.get(f"{property}_invert"):
                constraint = ~constraint
            constraints.append(constraint)
        return constraints

    def filtering_relationship_constraints(self, query, model, **kwargs):
        table = models[model]
        constraint_dict = {**kwargs.get("form", {}), **kwargs.get("constraints", {})}
        for related_model, relation_properties in relationships[model].items():
            related_table = aliased(models[relation_properties["model"]])
            match = constraint_dict.get(f"{related_model}_filter")
            if match == "empty":
                query = query.filter(~getattr(table, related_model).any())
            else:
                relation_ids = [
                    int(id) for id in constraint_dict.get(related_model, [])
                ]
                if not relation_ids:
                    continue
                query = (
                    query.join(related_table, getattr(table, related_model))
                    .filter(related_table.id.in_(relation_ids))
                    .group_by(table.id)
                )
        return query

    def filtering(self, model, bulk=False, rbac="read", username=None, **kwargs):
        table, query = models[model], db.query(model, rbac, username)
        total_records = query.with_entities(table.id).count()
        try:
            constraints = self.filtering_base_constraints(model, **kwargs)
        except regex_error:
            return {"error": "Invalid regular expression as search parameter."}
        constraints.extend(table.filtering_constraints(**kwargs))
        query = self.filtering_relationship_constraints(query, model, **kwargs)
        query = query.filter(and_(*constraints))
        filtered_records = query.with_entities(table.id).count()
        if bulk:
            instances = query.all()
            if bulk == "object":
                return instances
            else:
                return [getattr(instance, bulk) for instance in instances]
        data = kwargs["columns"][int(kwargs["order"][0]["column"])]["data"]
        ordering = getattr(getattr(table, data, None), kwargs["order"][0]["dir"], None)
        if ordering:
            query = query.order_by(ordering())
        table_result = {
            "draw": int(kwargs["draw"]),
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": [
                obj.table_properties(**kwargs)
                for obj in query.limit(int(kwargs["length"]))
                .offset(int(kwargs["start"]))
                .all()
            ],
        }
        if kwargs.get("export"):
            table_result["full_result"] = [
                obj.table_properties(**kwargs) for obj in query.all()
            ]
        if kwargs.get("clipboard"):
            table_result["full_result"] = ",".join(obj.name for obj in query.all())
        return table_result

    def get(self, model, id):
        return db.fetch(model, id=id).serialized

    def get_all(self, model):
        return [instance.get_properties() for instance in db.fetch_all(model)]

    def get_cluster_status(self):
        return [server.status for server in db.fetch_all("server")]

    def get_credentials(self, device, **kwargs):
        if kwargs["credentials"] == "device":
            credentials = device.get_credentials("any")
            return credentials.username, self.get_password(credentials.password)
        elif kwargs["credentials"] == "user":
            return current_user.name, self.get_password(current_user.password)
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
        device = db.fetch("device", id=device_id)
        return {
            property: app.custom.parse_configuration_property(device, property)
            for property in app.configuration_properties
        }

    def get_exported_services(self):
        return [f for f in listdir(app.path / "files" / "services") if ".tgz" in f]

    def get_git_content(self):
        repo = app.settings["app"]["git_repository"]
        if not repo:
            return
        local_path = app.path / "network_data"
        try:
            if exists(local_path):
                Repo(local_path).remotes.origin.pull()
            else:
                local_path.mkdir(parents=True, exist_ok=True)
                Repo.clone_from(repo, local_path)
        except Exception as exc:
            app.log("error", f"Git pull failed ({str(exc)})")
        self.update_database_configurations_from_git()

    def get_git_history(self, device_id):
        device = db.fetch("device", id=device_id)
        repo = Repo(self.path / "network_data")
        path = self.path / "network_data" / device.name
        return {
            data_type: [
                {"hash": str(commit), "date": commit.committed_datetime}
                for commit in list(repo.iter_commits(paths=path / data_type))
            ]
            for data_type in self.configuration_properties
        }

    def get_git_network_data(self, device_name, hash):
        commit, result = Repo(self.path / "network_data").commit(hash), {}
        device = db.fetch("device", name=device_name)
        for property in self.configuration_properties:
            try:
                file = commit.tree / device_name / property
                with BytesIO(file.data_stream.read()) as f:
                    value = f.read().decode("utf-8")
                result[property] = app.custom.parse_configuration_property(
                    device, property, value
                )
            except KeyError:
                result[property] = ""
        return result, commit.committed_datetime

    def get_migration_folders(self):
        return listdir(app.path / "files" / "migrations")

    def get_parent_workflows(self, workflow=None):
        yield workflow
        for parent_workflow in workflow.workflows:
            yield from self.get_parent_workflows(parent_workflow)

    def get_properties(self, model, id):
        return db.fetch(model, id=id).get_properties()

    def get_result(self, id):
        return db.fetch("result", id=id).result

    def get_runtimes(self, type, id):
        results = db.fetch("result", allow_none=True, all_matches=True, service_id=id)
        return sorted(set((result.parent_runtime,) * 2 for result in results))

    def get_service_logs(self, service, runtime, start_line):
        log_instance = db.fetch(
            "service_log", allow_none=True, runtime=runtime, service_id=service
        )
        number_of_lines = 0
        if log_instance:
            logs = log_instance.content
        else:
            lines = (
                app.log_queue(runtime, service, start_line=int(start_line), mode="get")
                or []
            )
            number_of_lines, logs = len(lines), "\n".join(lines)
        return {
            "logs": logs,
            "refresh": not log_instance,
            "line": int(start_line) + number_of_lines,
        }

    def get_service_state(self, path, runtime=None):
        service_id, state = path.split(">")[-1], None
        service = db.fetch("service", id=service_id, allow_none=True)
        if not service:
            raise db.rbac_error
        runs = db.query("run").filter(models["run"].services.any(id=service_id)).all()
        if runtime != "normal" and runs:
            if runtime == "latest":
                run = sorted(runs, key=attrgetter("runtime"), reverse=True)[0]
            else:
                run = db.fetch("run", parent_runtime=runtime)
            state = run.get_state()
        return {
            "service": service.to_dict(include=["services", "edges", "superworkflow"]),
            "runtimes": sorted(set((r.parent_runtime, r.creator) for r in runs)),
            "state": state,
            "runtime": runtime,
        }

    def get_session_log(self, session_id):
        return db.fetch("session", id=session_id).content

    def get_top_level_workflows(self):
        return [
            workflow.base_properties
            for workflow in db.fetch_all("workflow")
            if not workflow.workflows
        ]

    def get_tree_files(self, path):
        if path == "root":
            path = app.settings["paths"]["files"] or app.path / "files"
        else:
            path = path.replace(">", "/")
        return [
            {
                "a_attr": {"style": "width: 100%"},
                "data": {
                    "modified": ctime(getmtime(str(file))),
                    "path": str(file),
                    "name": file.name,
                },
                "text": file.name,
                "children": file.is_dir(),
                "type": "folder" if file.is_dir() else "file",
            }
            for file in Path(path).iterdir()
        ]

    def get_visualization_pools(self, view):
        return [
            pool.base_properties
            for pool in db.fetch_all("pool")
            if (view == "force_directed_view" and pool.devices and pool.links)
            or (view == "geographical_view" and (pool.devices or pool.links))
        ]

    def get_workflow_results(self, workflow, runtime):
        run = db.fetch("run", parent_runtime=runtime)
        state = run.state

        def rec(service, path=str(run.service_id)):
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
            color = "32CD32" if all(result.success for result in results) else "FF6666"
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

        return rec(run.service)

    def get_workflow_services(self, id, node):
        parents = list(self.get_parent_workflows(db.fetch("workflow", id=id)))
        if node == "all":
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
                        for workflow in db.fetch_all("workflow")
                        if not workflow.workflows
                    ),
                    key=itemgetter("text"),
                )
            )
        elif node == "standalone":
            return sorted(
                (
                    {
                        "data": {"id": service.id},
                        "text": service.scoped_name,
                        "a_attr": {"style": ("color: #6666FF;" "width: 100%")},
                    }
                    for service in db.fetch_all("service")
                    if not service.workflows and service.type != "workflow"
                ),
                key=itemgetter("text"),
            )
        elif node == "shared":
            return sorted(
                (
                    {
                        "data": {"id": service.id},
                        "text": service.scoped_name,
                        "a_attr": {"style": ("color: #FF1694;" "width: 100%")},
                    }
                    for service in db.fetch_all("service")
                    if service.shared and service.scoped_name not in ("Start", "End")
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

    def get_workflow_tree(self, full_path):
        path_id = full_path.split(">")

        def rec(service, path=""):
            path += ">" * bool(path) + str(service.id)
            if service.scoped_name in ("Start", "End"):
                return
            elif service.scoped_name == "Placeholder" and len(path_id) > 1:
                service = db.fetch("workflow", id=path_id[1])
            return {
                "data": {"path": path, **service.base_properties},
                "id": service.id,
                "state": {"opened": full_path.startswith(path)},
                "text": service.scoped_name,
                "children": sorted(
                    filter(None, [rec(child, path) for child in service.services]),
                    key=lambda node: node["text"].lower(),
                )
                if service.type == "workflow"
                else False,
                "a_attr": {
                    "class": "no_checkbox",
                    "style": (
                        f"color: #{'FF1694' if service.shared else '6666FF'};"
                        "width: 100%"
                    ),
                },
                "type": service.type,
            }

        return rec(db.fetch("workflow", id=path_id[0]))

    def load_debug_snippets(self):
        snippets = {}
        for path in Path(app.path / "files" / "snippets").glob("**/*.py"):
            with open(path, "r") as file:
                snippets[path.name] = file.read()
        return snippets

    def migration_export(self, **kwargs):
        for cls_name in kwargs["import_export_types"]:
            path = app.path / "files" / "migrations" / kwargs["name"]
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
        status, models = "Import successful.", kwargs["import_export_types"]
        empty_database = kwargs.get("empty_database_before_import", False)
        if empty_database:
            db.delete_all(*models)
        relations = defaultdict(lambda: defaultdict(dict))
        for model in models:
            path = app.path / "files" / folder / kwargs["name"] / f"{model}.yaml"
            if not path.exists():
                continue
            with open(path, "r") as migration_file:
                instances = yaml.load(migration_file)
                for instance in instances:
                    instance_type, relation_dict = instance.pop("type", model), {}
                    for related_model, relation in relationships[instance_type].items():
                        relation_dict[related_model] = instance.pop(related_model, [])
                    for property, value in instance.items():
                        if property in db.private_properties_set:
                            instance[property] = app.get_password(value)
                    try:
                        instance = db.factory(
                            instance_type,
                            migration_import=True,
                            no_fetch=empty_database,
                            update_pools=kwargs.get("update_pools", False),
                            import_mechanism=True,
                            **instance,
                        )
                        relations[instance_type][instance.name] = relation_dict
                    except Exception:
                        info(f"{str(instance)} could not be imported:\n{format_exc()}")
                        status = "Partial import (see logs)."
            db.session.commit()
        for model, instances in relations.items():
            for instance_name, related_models in instances.items():
                for property, value in related_models.items():
                    if not value:
                        continue
                    relation = relationships[model][property]
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
                        status = "Partial import (see logs)."
        db.session.commit()
        if not kwargs.get("skip_model_update"):
            for model in ("access", "service", "workflow_edge"):
                for instance in db.fetch_all(model):
                    instance.update()
        if not kwargs.get("skip_pool_update"):
            for pool in db.fetch_all("pool"):
                pool.compute_pool()
        app.log("info", status)
        return status

    def multiselect_filtering(self, model, **params):
        table = models[model]
        results = db.query(model).filter(table.name.contains(params.get("term")))
        return {
            "items": [
                {"text": result.ui_name, "id": str(result.id)}
                for result in results.limit(10)
                .offset((int(params["page"]) - 1) * 10)
                .all()
            ],
            "total_count": results.count(),
        }

    def import_service(self, archive):
        service_name = archive.split(".")[0]
        path = app.path / "files" / "services"
        with open_tar(path / archive) as tar_file:
            tar_file.extractall(path=path)
            status = self.migration_import(
                folder="services",
                name=service_name,
                import_export_types=["service", "workflow_edge"],
                skip_pool_update=True,
                skip_model_update=True,
                update_pools=True,
            )
        rmtree(path / service_name, ignore_errors=True)
        return status

    def import_topology(self, **kwargs):
        file = kwargs["file"]
        if kwargs["replace"]:
            db.delete_all("device")
        result = self.topology_import(file)
        info("Inventory import: Done.")
        return result

    def objectify(self, model, instance):
        for property, relation in relationships[model].items():
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
        getattr(target, kwargs["relation"]["relation"]["to"]).remove(instance)
        self.update_rbac(instance)

    def result_log_deletion(self, **kwargs):
        date_time_object = datetime.strptime(kwargs["date_time"], "%d/%m/%Y %H:%M:%S")
        date_time_string = date_time_object.strftime("%Y-%m-%d %H:%M:%S.%f")
        for model in kwargs["deletion_types"]:
            if model == "run":
                field_name = "runtime"
            elif model == "changelog":
                field_name = "time"
            session_query = db.session.query(models[model]).filter(
                getattr(models[model], field_name) < date_time_string
            )
            session_query.delete(synchronize_session=False)
            db.session.commit()

    @staticmethod
    def run(service, **kwargs):
        run_kwargs = {
            key: kwargs.pop(key)
            for key in (
                "trigger",
                "creator",
                "start_services",
                "runtime",
                "task",
                "target_devices",
                "target_pools",
            )
            if kwargs.get(key)
        }
        restart_run = db.fetch(
            "run",
            allow_none=True,
            runtime=kwargs.get("restart_runtime"),
        )
        if restart_run:
            run_kwargs["restart_run"] = restart_run
        service = db.fetch("service", id=service)
        service.status = "Running"
        initial_payload = kwargs.get("initial_payload", service.initial_payload)
        if service.type == "workflow" and service.superworkflow:
            run_kwargs["placeholder"] = run_kwargs["start_service"] = service.id
            service = service.superworkflow
            initial_payload.update(service.initial_payload)
        else:
            run_kwargs["start_service"] = service.id
        run = db.factory("run", service=service.id, commit=True, **run_kwargs)
        run.properties = kwargs
        return run.run({**initial_payload, **kwargs})

    def run_debug_code(self, **kwargs):
        result = StringIO()
        with redirect_stdout(result):
            try:
                environment = {"app": self, "db": db, "models": models}
                exec(kwargs["code"], environment)
            except Exception:
                return format_exc()
        return result.getvalue()

    def run_service(self, path, **kwargs):
        if isinstance(kwargs.get("start_services"), str):
            kwargs["start_services"] = kwargs["start_services"].split("-")
        service_id = str(path).split(">")[-1]
        for property in ("user", "csrf_token", "form_type"):
            kwargs.pop(property, None)
        kwargs["creator"] = getattr(current_user, "name", "")
        service = db.fetch("service", id=service_id, rbac="run")
        kwargs["runtime"] = runtime = app.get_time()
        if kwargs.get("asynchronous", True):
            Thread(target=self.run, args=(service_id,), kwargs=kwargs).start()
        else:
            service.run(runtime=runtime)
        return {
            "service": service.serialized,
            "runtime": runtime,
            "user": current_user.name,
        }

    def run_service_on_targets(self, **kwargs):
        return self.run_service(
            kwargs["service"],
            **{f"target_{kwargs['type']}s": kwargs["targets"].split("-")},
        )

    def save_file(self, filepath, **kwargs):
        if kwargs.get("file_content"):
            with open(Path(filepath.replace(">", "/")), "w") as file:
                return file.write(kwargs["file_content"])

    def save_positions(self, workflow_id, **kwargs):
        now, old_position = app.get_time(), None
        workflow = db.fetch("workflow", allow_none=True, id=workflow_id, rbac="edit")
        if not workflow:
            return
        for id, position in kwargs.items():
            new_position = [position["x"], position["y"]]
            if "-" not in id:
                service = db.fetch("service", id=id, rbac=None)
                old_position = service.positions.get(workflow.name)
                service.positions[workflow.name] = new_position
            elif id in workflow.labels:
                old_position = workflow.labels[id].pop("positions")
                workflow.labels[id] = {"positions": new_position, **workflow.labels[id]}
            if new_position != old_position:
                workflow.last_modified = now
        return now

    def save_settings(self, **kwargs):
        app.settings = kwargs["settings"]
        if kwargs["save"]:
            with open(app.path / "setup" / "settings.json", "w") as file:
                dump(kwargs["settings"], file, indent=2)

    def save_view_positions(self, **kwargs):
        for node_id, position in kwargs.items():
            db.factory("view_object", id=node_id, **position)
        return app.get_time()

    def scan_cluster(self, **kwargs):
        protocol = app.settings["cluster"]["scan_protocol"]
        for ip_address in IPv4Network(app.settings["cluster"]["scan_subnet"]):
            try:
                server = http_get(
                    f"{protocol}://{ip_address}/rest/is_alive",
                    timeout=app.settings["cluster"]["scan_timeout"],
                ).json()
                if app.settings["cluster"]["id"] != server.pop("cluster_id"):
                    continue
                db.factory("server", **{**server, **{"ip_address": str(ip_address)}})
            except ConnectionError:
                continue

    def scan_playbook_folder(self):
        path = Path(
            app.settings["paths"]["playbooks"] or app.path / "files" / "playbooks"
        )
        playbooks = [[str(f) for f in path.glob(e)] for e in ("*.yaml", "*.yml")]
        return sorted(sum(playbooks, []))

    def scheduler_action(self, mode, **kwargs):
        for task_id in self.filtering("task", bulk="id", form=kwargs):
            self.task_action(mode, task_id)

    def search_workflow_services(self, *args, **kwargs):
        return [
            "standalone",
            "shared",
            *[
                workflow.name
                for workflow in db.fetch_all("workflow")
                if any(
                    kwargs["str"].lower() in service.scoped_name.lower()
                    for service in workflow.services
                )
            ],
        ]

    def skip_services(self, workflow_id, service_ids):
        services = [db.fetch("service", id=id) for id in service_ids.split("-")]
        workflow = db.fetch("workflow", id=workflow_id)
        skip = not all(service.skip.get(workflow.name) for service in services)
        for service in services:
            service.skip[workflow.name] = skip
        workflow.last_modified = app.get_time()
        return {
            "skip": "skip" if skip else "unskip",
            "update_time": workflow.last_modified,
        }

    def stop_workflow(self, runtime):
        run = db.fetch("run", allow_none=True, runtime=runtime)
        if run and run.status == "Running":
            if app.redis_queue:
                app.redis("set", f"stop/{run.parent_runtime}", "true")
            else:
                app.run_stop[run.parent_runtime] = True
            return True

    def switch_menu(self, user_id):
        user = db.fetch("user", rbac=None, id=user_id)
        user.small_menu = not user.small_menu

    def switch_theme(self, user_id, theme):
        db.fetch("user", rbac=None, id=user_id).theme = theme

    def task_action(self, mode, task_id):
        return db.fetch("task", id=task_id, rbac="schedule").schedule(mode)

    def topology_export(self, **kwargs):
        workbook = Workbook()
        filename = kwargs["export_filename"]
        if "." not in filename:
            filename += ".xls"
        for obj_type in ("device", "link"):
            sheet = workbook.add_sheet(obj_type)
            for index, property in enumerate(model_properties[obj_type]):
                if property in db.dont_migrate[obj_type]:
                    continue
                sheet.write(0, index, property)
                for obj_index, obj in enumerate(db.fetch_all(obj_type), 1):
                    value = getattr(obj, property)
                    if type(value) == bytes:
                        value = str(app.decrypt(value), "utf-8")
                    sheet.write(obj_index, index, str(value))
        workbook.save(app.path / "files" / "spreadsheets" / filename)

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
                    func = db.field_conversion[property_types.get(property, "str")]
                    values[property] = func(sheet.row_values(row_index)[index])
                try:
                    db.factory(obj_type, **values).serialized
                except Exception as exc:
                    info(f"{str(values)} could not be imported ({str(exc)})")
                    status = "Partial import (see logs)."
            db.session.commit()
        for pool in db.fetch_all("pool"):
            pool.compute_pool()
        app.log("info", status)
        return status

    def update(self, type, **kwargs):
        try:
            kwargs.update(
                {
                    "last_modified": app.get_time(),
                    "update_pools": True,
                    "must_be_new": kwargs.get("id") == "",
                }
            )
            for arg in ("name", "scoped_name"):
                if arg in kwargs:
                    kwargs[arg] = kwargs[arg].strip()
            if kwargs["must_be_new"]:
                kwargs["creator"] = kwargs["user"] = getattr(current_user, "name", "")
            instance = db.factory(type, **kwargs)
            if kwargs.get("copy"):
                db.fetch(type, id=kwargs["copy"]).duplicate(clone=instance)
            db.session.flush()
            return instance.serialized
        except db.rbac_error:
            return {"alert": "Error 403 - Operation not allowed."}
        except Exception as exc:
            db.session.rollback()
            if isinstance(exc, IntegrityError):
                alert = (
                    f"There is already a {instance.class_type} "
                    "with the same parameters."
                )
                return {"alert": alert}
            app.log("error", format_exc())
            return {"alert": str(exc)}

    def update_all_pools(self):
        for pool in db.fetch_all("pool"):
            pool.compute_pool()

    def update_database_configurations_from_git(self):
        for dir in scandir(app.path / "network_data"):
            device = db.fetch("device", allow_none=True, name=dir.name)
            timestamp_path = Path(dir.path) / "timestamps.json"
            if not device:
                continue
            try:
                with open(timestamp_path) as file:
                    timestamps = load(file)
            except Exception:
                timestamps = {}
            for property in app.configuration_properties:
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
                for property in app.configuration_properties
            ):
                pool.compute_pool()

    def upload_files(self, **kwargs):
        file = kwargs["file"]
        file.save(f"{kwargs['folder']}/{file.filename}")

    def update_pool(self, pool_id):
        db.fetch("pool", id=int(pool_id), rbac="edit").compute_pool()

    def update_rbac(self, *instances):
        for instance in instances:
            if instance.type != "user":
                continue
            instance.update_rbac()

    def view_filtering(self, **kwargs):
        return {
            f"{model}s": self.filtering(model, **kwargs[model], bulk="view_properties")
            for model, form in kwargs.items()
        }

    def web_connection(self, device_id, **kwargs):
        if not self.settings["ssh"]["credentials"][kwargs["credentials"]]:
            return {"alert": "Unauthorized authentication method."}
        session = str(uuid4())
        device = db.fetch("device", id=device_id, rbac="connect")
        self.ssh_sessions[session] = {
            "device": device.id,
            "form": kwargs,
            "user": current_user.name,
        }
        if "authentication" in kwargs:
            credentials = self.get_credentials(device, **kwargs)
            self.ssh_sessions[session]["credentials"] = credentials
        return {"device": device.name, "session": session}
