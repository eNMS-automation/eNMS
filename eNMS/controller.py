from black import format_str, Mode
from collections import defaultdict
from contextlib import redirect_stdout
from datetime import datetime
from difflib import unified_diff
from dramatiq import actor
from flask_login import current_user
from functools import wraps
from git import Repo
from io import BytesIO, StringIO
from itertools import batched
from json import dump, load
from logging import error, info
from operator import itemgetter
from orjson import dumps, loads, OPT_INDENT_2, OPT_SORT_KEYS
from os import getenv, listdir, makedirs, scandir
from os.path import exists, splitext
from pathlib import Path
from re import compile, search, sub
from sqlalchemy import and_, cast, func, insert, or_, select, String, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import ScalarObjectAttributeImpl as ScalarAttr
from sqlalchemy.orm.strategies import DeferredColumnLoader
from sqlalchemy.sql.expression import true
from subprocess import Popen
from threading import Thread
from traceback import format_exc
from uuid import uuid4
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

from eNMS.database import db
from eNMS.environment import env
from eNMS.forms import form_factory
from eNMS.variables import vs


class Controller(vs.TimingMixin):
    def _initialize(self, first_init):
        if not first_init:
            return
        import_folder = vs.settings["app"].get("startup_migration", "default")
        self.json_migration_import(name=import_folder)
        if vs.settings.get("on_startup", {}).get("get_git_content"):
            self.get_git_content(force_update=True)
        if vs.settings.get("on_startup", {}).get("scan_folder"):
            self.scan_folder()

    def _register_endpoint(self, func):
        setattr(self, func.__name__, func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    def add_edge(self, workflow_id, subtype, source, destination):
        workflow = db.fetch("workflow", id=workflow_id, rbac="edit")
        existing_edge = db.fetch(
            "workflow_edge",
            subtype=subtype,
            source_id=source,
            destination_id=destination,
            workflow_id=workflow_id,
            allow_none=True,
        )
        if existing_edge:
            if existing_edge.soft_deleted:
                db.delete_instance(existing_edge)
                db.session.commit()
            else:
                return {"alert": f"There is already a '{subtype}' workflow edge."}
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
        target = db.fetch(
            kwargs["target_type"], name=kwargs["target_name"], rbac="edit"
        )
        if target.type == "pool" and not target.manually_defined:
            return {"alert": "Adding objects to a dynamic pool is not allowed."}
        model, property = kwargs["model"], kwargs["property"]
        instances = set(db.fetch_all(model, id_in=kwargs.get("instances", [])))
        if kwargs["names"]:
            names = [instance.strip() for instance in kwargs["names"].split(",")]
            instance_objects = set(db.fetch_all(model, name_in=names))
            object_names = {instance.name for instance in instance_objects}
            if diff := set(names) - object_names:
                return {"alert": f"These {model}s do not exist: {', '.join(diff)}."}
            instances |= instance_objects
        instances = instances - set(getattr(target, property))
        for instance in instances:
            getattr(target, property).append(instance)
        target.last_modified = vs.get_time()
        target.last_modified_by = current_user.name
        return {"number": len(instances), "target": target.base_properties}

    def add_objects_to_network(self, network_id, **kwargs):
        network = db.fetch("network", id=network_id)
        result = {"devices": [], "links": []}
        devices = set(db.fetch_all("device", id_in=kwargs["devices"]))
        links = set(db.fetch_all("link", id_in=kwargs["links"]))
        for pool in db.fetch_all("pool", id_in=kwargs["pools"]):
            devices |= set(pool.devices)
            links |= set(pool.links)
        if kwargs["add_connected_devices"]:
            for link in links:
                devices |= {link.source, link.destination}
        if kwargs["add_connected_links"]:
            for device in devices:
                links |= set(device.get_neighbors("link"))
        for device in devices:
            if not device or device in network.devices or device == network:
                continue
            result["devices"].append(device.get_properties())
            network.devices.append(device)
        for link in links:
            if link in network.links:
                continue
            if (
                link.source not in network.devices
                or link.destination not in network.devices
            ):
                continue
            result["links"].append(link.get_properties())
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
                    objects = db.fetch_all(related_model, id_in=value)
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

    def compare(self, type, id, v1, v2, context_lines):
        if type == "changelog":
            properties = db.fetch("changelog", id=id).history["properties"][v1]
            first, second, v1, v2 = properties["old"], properties["new"], "Old", "New"
        elif id == "none":
            first = getattr(db.fetch("device", id=v1), type)
            second = getattr(db.fetch("device", id=v2), type)
        elif type in ("result", "device_result"):
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
                str(first).splitlines(),
                str(second).splitlines(),
                fromfile=f"V1 ({v1})",
                tofile=f"V2 ({v2})",
                lineterm="",
                n=int(context_lines),
            )
        )

    def copy_service_in_workflow(self, workflow_id, **kwargs):
        service_sets = list(set(kwargs["services-to-copy"].split(",")))
        service_instances = db.fetch_all("service", id_in=service_sets)
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
            "services": [service.get_properties() for service in services],
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
                "task": len(
                    db.fetch_all("task", properties=["id"], rbac=None, is_active=True)
                ),
                "workflow": active_workflow,
            },
            "properties": {
                model: self.counters(vs.properties["dashboard"][model][0], model)
                for model in vs.properties["dashboard"]
            },
        }

    def counters(self, property, model):
        return dict(
            db.query(model, rbac=None)
            .with_entities(getattr(vs.models[model], property), func.count())
            .group_by(getattr(vs.models[model], property))
        )

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
        env.log(
            "info",
            f"Adding label '{kwargs['text']}' to '{workflow}'",
            instance=workflow,
        )
        return {"id": label_id, **label}

    def delete_builder_selection(self, type, id, **selection):
        instance = db.fetch(type, id=id)
        instance.update_last_modified_properties()
        if type == "workflow":
            instance.check_restriction_to_owners("edit")
        names = defaultdict(list)
        for edge_id in selection["edges"]:
            if type == "workflow":
                edge = db.fetch("workflow_edge", id=edge_id)
                edge.soft_deleted = True
                names["links"].append(edge.name)
            else:
                instance.links.remove(db.fetch("link", id=edge_id))
        for node_id in selection["nodes"]:
            if isinstance(node_id, str):
                names["labels"].append(instance.labels.pop(node_id)["content"])
            elif type == "network":
                instance.devices.remove(db.fetch("device", id=node_id))
            else:
                service = db.fetch("service", rbac="edit", id=node_id)
                names["services"].append(service.name)
                if not service.shared:
                    service.soft_deleted = True
                else:
                    instance.services.remove(service)
        log = " - ".join(f"{k.capitalize()}: {', '.join(v)}" for k, v in names.items())
        env.log("info", f"Removed from '{instance}': {log}", instance=instance)
        return instance.last_modified

    def delete_corrupted_objects(self):
        number_of_corrupted_services = 0
        for service in db.fetch_all("service", shared=False):
            if service.workflows or service.name == service.scoped_name:
                continue
            db.session.delete(service)
            number_of_corrupted_services += 1
        db.session.commit()
        env.log(
            "warning",
            f"Number of corrupted services deleted: {number_of_corrupted_services}",
        )
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
                or edge.soft_deleted
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
        db.session.commit()
        env.log(
            "warning", f"Number of corrupted edges deleted: {number_of_corrupted_edges}"
        )

    def delete_instance(self, model, instance_id):
        try:
            return db.delete(model, id=instance_id)
        except db.rbac_error:
            return {"alert": "Error 403 - Not Authorized."}
        except Exception as exc:
            return {"alert": f"Unable to delete {model} ({exc})"}

    def delete_soft_deleted_objects(self):
        soft_deleted_edges = db.fetch_all("workflow_edge", soft_deleted=True)
        for edge in soft_deleted_edges:
            db.delete_instance(edge)
        db.session.commit()
        soft_deleted_services = db.fetch_all("service", soft_deleted=True)
        for service in soft_deleted_services:
            db.delete_instance(service)
        db.session.commit()
        env.log("warning", "Soft-deleted objects successfully deleted")

    def edit_file(self, filepath):
        scoped_path = filepath.replace(">", "/")
        file = db.fetch("file", path=scoped_path)
        try:
            with open(f"{vs.file_path}{scoped_path}") as file:
                return file.read()
        except FileNotFoundError:
            file.status = "Not Found"
            return {"error": "File not found on disk."}
        except UnicodeDecodeError:
            return {"error": "Cannot read file (unsupported type)."}

    def filtering(
        self, model, bulk=False, rbac="read", user=None, properties=None, **kwargs
    ):
        table, pagination = vs.models[model], kwargs.get("pagination")
        query = db.query(model, rbac, user, properties=properties)
        total_records, filtered_records = (10**6,) * 2
        if pagination and not bulk and not properties:
            total_records = query.with_entities(table.id).count()
        constraints = self.filtering_base_constraints(model, **kwargs)
        constraints.extend(table.filtering_constraints(**kwargs))
        constraints.extend(kwargs.get("sql_contraints", []))
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
            table_result["clipboard"] = ",".join(obj.name for obj in query.all())
        return table_result

    def filtering_base_constraints(self, model, **kwargs):
        table, constraints = vs.models[model], []
        constraint_dict = {**kwargs.get("form", {}), **kwargs.get("constraints", {})}
        if serialized := constraint_dict.get("serialized"):
            deferred_columns = {
                attr.key
                for attr in inspect(table).column_attrs
                if isinstance(attr.strategy, DeferredColumnLoader)
            }
            constraints.append(
                or_(
                    *(
                        column.ilike(f"%{serialized}%")
                        for column in inspect(table).columns
                        if isinstance(column.type, String)
                        and column.name not in deferred_columns
                    )
                )
            )
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
            is_scalar = isinstance(getattr(table, related_model).impl, ScalarAttr)
            match = constraint_dict.get(f"{related_model}_filter")
            invert = constraint_dict.get(f"{related_model}_invert")
            if match == "empty":
                func = "has" if is_scalar else "any"
                constraint = getattr(getattr(table, related_model), func)()
                query = query.filter(constraint if invert else ~constraint)
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

    def format_code_with_black(self, content):
        return format_str(content, mode=Mode())

    def get(self, model, id, **kwargs):
        func = "get_properties" if kwargs.pop("properties_only", None) else "to_dict"
        if func == "to_dict":
            kwargs["include"] = list(vs.form_properties[model])
            kwargs["include_relations"] = list(vs.form_properties[model])
        return getattr(db.fetch(model, id=id), func)(**kwargs)

    def get_builder_children(self, type, instance_id):
        instance = db.fetch(type, id=instance_id)
        children = {instance.name}
        child_property = "services" if type == "workflow" else "devices"

        def rec(instance):
            for sub_instance in getattr(instance, child_property):
                children.add(sub_instance.name)
                if sub_instance.type == type:
                    rec(sub_instance)

        rec(instance)
        return list(children)

    def get_changelog_history(self, changelog_id):
        changelog = db.fetch("changelog", id=changelog_id)
        return {"content": changelog.content, "history": changelog.history}

    def get_cluster_status(self):
        return [server.status for server in db.fetch_all("server")]

    def get_credentials(self, device, optional=False, **kwargs):
        if kwargs["credentials"] == "custom":
            return kwargs["username"], kwargs["password"]
        else:
            credential = (
                db.get_credential(current_user.name, device=device, optional=optional)
                if kwargs["credentials"] == "device"
                else db.fetch("credential", id=kwargs["named_credential"])
            )
            if not credential:
                return
            return credential.username, env.get_password(credential.password)

    def get_device_network_data(self, device_id):
        device = db.fetch("device", id=device_id, rbac="configuration")
        return {
            property: vs.custom.parse_configuration_property(device, property)
            for property in vs.configuration_properties
        }

    def get_form_properties(self, service_id):
        form_factory.register_parameterized_form(service_id)
        return vs.form_properties[f"initial-{service_id}"]

    def get_git_content(self, force_update=False):
        env.log("info", "Starting Git Content Update")
        repo = vs.settings["app"]["git_repository"]
        if not repo:
            return
        local_path = vs.path / vs.automation["configuration_backup"]["folder"]
        try:
            if exists(local_path):
                Repo(local_path).remotes.origin.pull()
            else:
                local_path.mkdir(parents=True, exist_ok=True)
                Repo.clone_from(repo, local_path)
        except Exception as exc:
            env.log("error", f"Git pull failed ({str(exc)})")
        try:
            self.update_database_configurations_from_git(force_update)
        except Exception as exc:
            env.log("error", f"Update of device configurations failed ({str(exc)})")
        env.log("info", "Git Content Update Successful")

    def get_git_history(self, device_id):
        device = db.fetch("device", id=device_id, rbac="configuration")
        folder = vs.automation["configuration_backup"]["folder"]
        repo = Repo(vs.path / folder)
        path = vs.path / folder / device.name
        return {
            data_type: [
                {"hash": str(commit), "date": commit.committed_datetime}
                for commit in list(repo.iter_commits(paths=path / data_type))
            ]
            for data_type in vs.configuration_properties
        }

    def get_git_network_data(self, device_name, hash):
        folder = vs.automation["configuration_backup"]["folder"]
        commit, result = Repo(vs.path / folder).commit(hash), {}
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

    def get_instance_tree(self, type, full_path, runtime=None, **kwargs):
        path_id = full_path.split(">")
        path_pid = [db.fetch(type, id=id, rbac=None).persistent_id for id in path_id]
        full_ppath = ">".join(path_pid)
        run = db.fetch("run", runtime=runtime) if runtime else None
        state = {}
        if "state" in kwargs:
            state = kwargs["state"]
        elif run:
            state = run.state or run.get_state()
        highlight = []

        def match(instance, **kwargs):
            is_regex_search = kwargs.get("regex_search", False)
            name = getattr(instance, "name" if type == "network" else "scoped_name")
            value = kwargs["search_value"]
            if kwargs["search_mode"] == "names":
                is_match = (
                    search(value, name)
                    if is_regex_search
                    else value.lower() in name.lower()
                )
            else:
                serialized = str(instance.get_properties().values())
                is_match = (
                    search(value, serialized)
                    if is_regex_search
                    else value.lower() in serialized.lower()
                )
            if is_match:
                highlight.append(instance.id)
            return is_match

        def rec(instance, path):
            if run and path not in state:
                return
            local_path_ids = path.split(">")
            if (
                getattr(instance, "run_method", None) == "per_device"
                and "device_state" in kwargs
                and instance.id not in kwargs["device_state"]
            ):
                return
            style, active_search = "", kwargs.get("search_value")
            if type == "workflow":
                if instance.scoped_name in ("Start", "End"):
                    return
                elif instance.scoped_name == "Placeholder" and len(path_id) > 1:
                    instance = db.fetch(type, id=path_id[1])
                    path = f"{path.split('>')[0]}>{instance.persistent_id}"
            if active_search and instance.type != type:
                if match(instance, **kwargs):
                    style = "font-weight: bold; color: #BABA06"
                elif not kwargs["display_all"]:
                    return
            children = False
            if instance.type == type:
                instances = (
                    instance.exclude_soft_deleted("services")
                    if type == "workflow"
                    else instance.devices
                )
                children_results = []
                for child in instances:
                    if str(child.persistent_id) in local_path_ids:
                        continue
                    if run and child.scoped_name == "Placeholder" and run.placeholder:
                        child = run.placeholder
                    child_results = rec(child, f"{path}>{child.persistent_id}")
                    if run and not child_results:
                        continue
                    children_results.append(child_results)
                children = sorted(
                    filter(None, children_results),
                    key=(
                        itemgetter("runtime")
                        if run
                        else lambda node: node["text"].lower()
                    ),
                )
                if active_search:
                    is_match = match(instance, **kwargs)
                    if not children and not is_match and not kwargs["display_all"]:
                        return
                    elif is_match:
                        style = "font-weight: bold; color: #BABA06"
            progress_data = {}
            if run and "device_state" not in kwargs:
                progress = state[path].get("progress")
                if progress and progress["device"]["total"]:
                    progress_data = {"progress": progress["device"]}
            if instance.id in kwargs.get("device_state", {}):
                color = kwargs["device_state"][instance.id]
            elif run:
                if state[path].get("dry_run"):
                    color = "#E09E2F"
                elif "success" in state[path]:
                    color = "#32CD32" if state[path]["success"] else "#FF6666"
                else:
                    color = "#25B6FA"
            else:
                color = (
                    "#FF1694"
                    if getattr(instance, "shared", False)
                    else "#E09E2F" if getattr(instance, "dry_run", False) else "#6666FF"
                )
            text = instance.scoped_name if type == "workflow" else instance.name
            attr_class = "jstree-wholerow-clicked" if full_ppath == path else ""
            runtime = state[path].get("runtime") if state else None
            return {
                "runtime": runtime,
                "data": {
                    "path": path,
                    "properties": instance.base_properties,
                    **progress_data,
                },
                "id": path,
                "state": {"opened": full_ppath.startswith(path)},
                "text": text if len(text) < 45 else f"{text[:45]}...",
                "children": children,
                "a_attr": {
                    "class": f"no_checkbox {attr_class}",
                    "style": f"color: {color}; width: 100%; {style}",
                },
                "type": instance.type,
            }

        # In a standard run, the top-level service in the path has run so we use it
        # as root of the tree. In case of restart run from a subworkflow or from a
        # workflow that has a superworkflow, we use the last service as root.
        if run:
            has_root_state = str(path_pid[0]) in state
            root_id = path_id[0] if has_root_state else path_id[-1]
            root_path = str(path_pid[0]) if has_root_state else full_ppath
        else:
            root_id, root_path = path_id[0], str(path_pid[0])
        return {
            "tree": rec(db.fetch(type, id=root_id), root_path),
            "highlight": highlight,
        }

    def get_migration_folders(self):
        return listdir(Path(vs.migration_path))

    def get_network_state(self, path, **kwargs):
        network = db.fetch("network", id=path.split(">")[-1], allow_none=True)
        if not network:
            raise db.rbac_error
        results = db.fetch_all("result", parent_runtime=kwargs.get("runtime"))
        output = {
            "network": network.to_dict(include_relations=["devices", "links"]),
            "device_results": {
                result.device_id: result.success
                for result in results
                if result.device_id
            },
        }
        if kwargs.get("get_tree") or kwargs.get("search_value"):
            output.update(self.get_instance_tree("network", path, **kwargs))
        return output

    def get_profiling_data(self):
        return vs.profiling

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
        service_alias = aliased(vs.models["service"])
        query = (
            db.query("run", properties=["name", "runtime"])
            .join(service_alias, vs.models["run"].services)
            .filter(service_alias.id == id)
        )
        if display == "user":
            query = query.filter(vs.models["run"].creator == current_user.name)
        return sorted(((run.runtime, run.name) for run in query.all()), reverse=True)

    def get_service_logs(self, service, runtime, line=0, device=None, search=None):
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
        if search:
            lines = [line for line in lines if search.lower() in line.lower()]
        return {
            "logs": "\n" + "\n".join(lines) if lines else "",
            "refresh": not log_instance,
            "line": int(line) + number_of_lines,
        }

    def get_service_state(self, path, **kwargs):
        state, run, path_id = None, None, path.split(">")
        runtime, display = kwargs.get("runtime"), kwargs.get("display")
        output = {"runtime": runtime}
        service = db.fetch("service", id=path_id[-1], allow_none=True)
        if len(path_id) == 1 and getattr(service, "superworkflow", None):
            path = f"{service.superworkflow.id}>{path}"
            path_id = path.split(">")
        if not service:
            raise db.rbac_error
        runs = db.query("run", properties=["name", "runtime"], rbac=None).filter(
            vs.models["run"].service_id.in_(path_id)
        )
        if display == "user":
            runs = runs.filter(vs.models["run"].creator == current_user.name)
        runs = runs.all()
        if runtime != "normal" and runs:
            if runtime == "latest":
                runtime = sorted(run.runtime for run in runs)[-1]
            run = db.fetch("run", allow_none=True, runtime=runtime)
            state = kwargs["state"] = run.get_state() if run else None
        if kwargs.get("device") and run:
            output["device_state"] = kwargs["device_state"] = {
                result.service_id: result.result.get(
                    "color", "#32CD32" if result.success else "#FF6666"
                )
                for result in db.fetch_all(
                    "result", parent_runtime=run.runtime, device_id=kwargs.get("device")
                )
            }
        kwargs["runtime"] = getattr(run, "runtime", None)
        if kwargs.get("search_value") and kwargs.get("regex_search"):
            try:
                compile(kwargs["search_value"])
            except Exception as exc:
                return {"alert": f"Invalid Regular Expression ('{exc}')"}
        if kwargs.get("get_tree") or kwargs.get("search_value"):
            output.update(self.get_instance_tree("workflow", path, **kwargs))
        serialized_service = service.to_dict(include_relations=["superworkflow"])
        run_properties = vs.automation["workflow"]["state_properties"]["run"]
        service_properties = vs.automation["workflow"]["state_properties"]["service"]
        if service.type == "workflow":
            serialized_service["edges"] = [
                edge.get_properties() for edge in service.exclude_soft_deleted("edges")
            ]
            serialized_service["services"] = []
            for subservice in service.exclude_soft_deleted("services"):
                properties = subservice.get_properties(include=service_properties)
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
        session = db.fetch("session", id=session_id)
        return session.content, session.device_name

    def get_store(self, **kwargs):
        store = None
        if "id" in kwargs:
            store = db.fetch("store", id=kwargs["id"])
        elif kwargs.get("path"):
            store = db.fetch("store", path=kwargs["path"])
        elif kwargs.get("parent") and kwargs["store"]["store_id"]:
            store = db.fetch("store", id=kwargs["store"]["store_id"])
        return store.get_properties() if store else None

    def get_time(self):
        return vs.get_time()

    def get_top_level_instances(self, type):
        result = defaultdict(list)
        constraints = [~getattr(vs.models[type], f"{type}s").any()]
        if type == "workflow":
            constraints.append(vs.models[type].shared == true())
        properties = ["id", "category", "name"]
        for instance in (
            db.query(type, properties=properties).filter(or_(*constraints)).all()
        ):
            entry = dict(zip(properties, instance))
            result[instance.category or "Other"].append(entry)
        return result

    def get_visualization_pools(self, view):
        has_device = vs.models["pool"].devices.any()
        has_link = vs.models["pool"].links.any()
        pools = db.query("pool").filter(or_(has_device, has_link)).all()
        return [pool.base_properties for pool in pools]

    def get_workflow_path(self, path):
        return ">".join(
            db.fetch("service", id=id).persistent_id for id in path.split(">")
        )

    def get_workflow_services(self, id, node, search=None):
        parents = {
            workflow.name for workflow in db.fetch("workflow", id=id).get_ancestors()
        }
        if node == "all" and not search:
            workflows = self.filtering(
                "workflow",
                properties=["id", "name"],
                constraints={"workflows_filter": "empty"},
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
                            "state": {"disabled": workflow.name in parents},
                            "a_attr": {
                                "class": (
                                    "no_checkbox" if workflow.name in parents else ""
                                ),
                                "style": "color: #6666FF; width: 100%",
                            },
                        }
                        for workflow in workflows
                    ),
                    key=itemgetter("text"),
                )
            )
        elif node == "all" and search:
            services = self.filtering(
                "service",
                properties=["id", "scoped_name", "type", "name", "shared"],
                constraints={"name": search, "soft_deleted": "bool-false"},
            )
            result = defaultdict(list)
            for service in services:
                if service.type != "workflow" and service.shared:
                    result["Shared services"].append(service)
                elif service.type != "workflow" and service.name == service.scoped_name:
                    result["Standalone services"].append(service)
                else:
                    if service.name != service.scoped_name:
                        name = service.name.replace(f" {service.scoped_name}", "")[1:-1]
                    else:
                        name = service.name
                    result[name].append(service)
            return [
                {
                    "text": key,
                    "type": "category",
                    "state": {"opened": True, "disabled": True},
                    "a_attr": {"class": "no_checkbox"},
                    "children": [
                        {
                            "id": service.name,
                            "data": {"id": service.id},
                            "text": service.scoped_name,
                            "a_attr": {
                                "style": (
                                    f"color: #{'FF1694' if service.shared else '6666FF'}"
                                    "; width: 100%"
                                ),
                            },
                            "type": (
                                "workflow" if service.type == "workflow" else "service"
                            ),
                        }
                        for service in services
                    ],
                }
                for key, services in result.items()
            ]
        elif node == "standalone":
            services = self.filtering(
                "service",
                properties=["id", "scoped_name"],
                constraints={
                    "workflows_filter": "empty",
                    "type": "service",
                    "shared": "bool-false",
                },
            )
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
            services = self.filtering(
                "service",
                properties=["id", "scoped_name"],
                constraints={"shared": "bool-true"},
            )
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
            services = db.fetch("workflow", id=node).exclude_soft_deleted("services")
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
                    for service in services
                    if service.scoped_name not in ("Start", "End")
                ),
                key=itemgetter("text"),
            )

    def import_topology(self, **kwargs):
        file = kwargs["file"]
        if kwargs["replace"]:
            db.delete_all("device")
        result = self.topology_import(file)
        info("Inventory import: Done.")
        return result

    def json_export_association(self, association_name, path, option):
        association_table = db.associations[association_name]
        table = association_table["table"]
        model1 = association_table["model1"]["foreign_key"]
        model2 = association_table["model2"]["foreign_key"]
        cls1 = aliased(vs.models[model1])
        cls2 = aliased(vs.models[model2])
        statement = select(getattr(cls1, "name"), getattr(cls2, "name")).select_from(
            table.join(cls1, getattr(table.c, f"{model1}_id") == cls1.id).join(
                cls2, getattr(table.c, f"{model2}_id") == cls2.id
            )
        )
        result = sorted((row[0], row[1]) for row in db.session.execute(statement).all())
        if not result:
            return
        with open(path / f"{association_name}.json", "wb") as file:
            file.write(dumps(result, option=option))

    def json_export_properties(self, cls_name, path, option):
        cls = vs.models[cls_name]
        export_type = getattr(cls, "export_type", cls.type)
        excluded_properties = set(
            db.json_migration["dont_migrate"].get(export_type, [])
        ) | {"type"}
        excluded_properties |= set(getattr(cls, "model_properties", {}))
        properties_to_export = [
            property
            for property in vs.model_properties[cls_name]
            if property not in excluded_properties
        ]
        instances = [
            dict(row._mapping)
            for row in db.query(
                cls_name, properties=properties_to_export, rbac=None
            ).all()
        ]
        if not instances:
            return
        if not exists(path):
            makedirs(path)
        with open(path / f"{cls_name}.json", "wb") as file:
            file.write(dumps(instances, option=option))

    def json_export_scalar(self, cls_name, path, option):
        for property, relation in vs.relationships[cls_name].items():
            if relation["list"]:
                continue
            if f"{cls_name}_{property}" in db.json_migration["no_export"]:
                continue
            cls = vs.models[cls_name]
            alias = aliased(vs.models[relation["model"]], flat=True)
            statement = (
                select(getattr(cls, "name"), getattr(alias, "name"))
                .select_from(cls)
                .join(alias, getattr(cls, f"{property}_id") == getattr(alias, "id"))
            )
            result = dict(db.session.execute(statement).all())
            filepath = path / f"{cls_name}_{property}.json"
            if not result and not exists(filepath):
                continue
            with open(filepath, "wb") as file:
                file.write(dumps(result, option=option))

    def json_import_associations(self, association_name, name_to_id, path):
        properties = db.associations[association_name]
        filepath = path / f"{association_name}.json"
        if not exists(filepath):
            return
        with open(filepath, "rb") as file:
            data = loads(file.read())
        model1 = properties["model1"]["foreign_key"]
        model2 = properties["model2"]["foreign_key"]
        export_model1 = getattr(vs.models[model1], "export_type", model1)
        export_model2 = getattr(vs.models[model2], "export_type", model2)
        for batch in batched(
            (
                {
                    f"{model1}_id": name_to_id[export_model1][name1],
                    f"{model2}_id": name_to_id[export_model2][name2],
                }
                for name1, name2 in data
            ),
            vs.database["transactions"]["batch_size"],
        ):
            db.session.execute(properties["table"].insert(), batch)

    def json_import_properties(self, cls_name, path):
        filepath = path / f"{cls_name}.json"
        if cls_name in db.json_migration["no_export"] or not exists(filepath):
            return
        with open(filepath, "rb") as file:
            instances = loads(file.read())
        for batch in batched(instances, vs.database["transactions"]["batch_size"]):
            db.session.execute(insert(vs.models[cls_name]), batch)

    def json_import_scalar(self, cls_name, name_to_id, path):
        updates = defaultdict(dict)
        export_model1 = getattr(vs.models[cls_name], "export_type", cls_name)
        for property, relation in vs.relationships[cls_name].items():
            filepath = path / f"{cls_name}_{property}.json"
            if relation["list"] or not exists(filepath):
                continue
            with open(filepath, "rb") as file:
                relations = loads(file.read())
            export_model2 = getattr(
                vs.models[relation["model"]], "export_type", relation["model"]
            )
            for source, destination in relations.items():
                source_id = name_to_id[export_model1][source]
                destination_id = name_to_id[export_model2][destination]
                updates[source_id][f"{property}_id"] = destination_id
        for batch in batched(
            ({"id": id, **values} for id, values in updates.items()),
            vs.database["transactions"]["batch_size"],
        ):
            db.session.execute(update(vs.models[cls_name]), list(batch))

    def json_migration_export(self, **kwargs):
        export_models = [
            class_name
            for class_name in vs.models
            if class_name not in db.json_migration["no_export"]
        ]
        option = (
            OPT_INDENT_2 | OPT_SORT_KEYS
            if kwargs.get("export_format") == "structured"
            else None
        )
        path = Path(vs.migration_path) / kwargs["name"]
        for cls_name in export_models:
            self.json_export_properties(cls_name, path, option)
            self.json_export_scalar(cls_name, path, option)
        for association_name in db.associations:
            self.json_export_association(association_name, path, option)
        with open("metadata.json", "wb") as file:
            metadata = {"version": vs.server_version, "export_time": datetime.now()}
            file.write(dumps(metadata))

    def json_migration_import(self, **kwargs):
        export_models = [
            class_name
            for class_name in vs.models
            if class_name not in db.json_migration["no_export"]
        ]
        with env.timer("Clean Database Before Importing"):
            for table_properties in db.associations.values():
                db.session.execute(table_properties["table"].delete())
            for cls_name in export_models:
                db.session.execute(vs.models[cls_name].__table__.delete())
            for cls_name in db.json_migration["clear_on_import"]:
                db.session.execute(vs.models[cls_name].__table__.delete())
            db.session.commit()
        path = Path(vs.migration_path) / kwargs["name"]
        with env.timer("Import Properties"):
            for cls_name in vs.models:
                self.json_import_properties(cls_name, path)
            db.session.commit()
        with env.timer("Name to ID Assocation"):
            name_to_id = {}
            for cls_name in db.json_migration["import_export_models"]:
                cls = vs.models[cls_name]
                name_to_id[cls_name] = dict(
                    db.session.execute(select(cls.name, cls.id)).all()
                )
        with env.timer("Import Scalar Properties"):
            for cls_name in vs.models:
                self.json_import_scalar(cls_name, name_to_id, path)
        with env.timer("Import Associations"):
            for association_name in db.associations:
                self.json_import_associations(association_name, name_to_id, path)
        db.session.commit()
        server = db.fetch("server", name=vs.server, rbac=None, allow_none=True)
        vs.server_id = getattr(server, "id", None)
        return "Import successful."

    def multiselect_filtering(self, model, **params):
        table = vs.models[model]
        query = db.query(model).filter(table.name.contains(params.get("term")))
        query = self.filtering_relationship_constraints(query, model, **params)
        query = query.filter(and_(*self.filtering_base_constraints(model, **params)))
        if "property" in params.get("order", {}):
            order_property = getattr(table, params["order"]["property"])
            order_direction = params["order"].get("direction", "asc")
            query = query.order_by(getattr(order_property, order_direction)())
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

    @staticmethod
    @actor(max_retries=0, time_limit=float("inf"))
    def run(service, **kwargs):
        run_object, user = None, kwargs["creator"]
        if "path" not in kwargs:
            kwargs["path"] = str(service)
        keys = list(vs.model_properties["run"]) + list(vs.relationships["run"])
        run_kwargs = {key: kwargs.pop(key) for key in keys if kwargs.get(key)}
        run_kwargs["is_async"] = kwargs.get("async", True)
        for property in ("name", "labels"):
            if property in kwargs.get("form", {}):
                run_kwargs[property] = kwargs["form"][property]
            else:
                run_kwargs.pop(property, None)
        service = db.fetch("service", id=service, rbac="run", user=user)
        initial_payload = {
            **service.initial_payload,
            **kwargs.get("form", {}).get("initial_payload", {}),
        }
        restart_runtime = kwargs.get("restart_runtime")
        restart_run = db.fetch(
            "run", allow_none=True, runtime=restart_runtime, user=user
        )
        if service.type == "workflow" and service.superworkflow and not restart_run:
            run_kwargs["placeholder"] = service.id
            run_kwargs["path"] = str(service.superworkflow.id)
            service = service.superworkflow
            initial_payload.update(service.initial_payload)
        if restart_run:
            run_kwargs["restart_run"] = restart_run.id
            initial_payload = restart_run.payload
        run_kwargs["services"] = [service.id]
        run_object = db.factory(
            "run",
            service=service.id,
            commit=True,
            must_be_new=True,
            rbac=None,
            **run_kwargs,
        )
        db.try_set(service, "status", "Running")
        db.try_set(service, "last_run", vs.get_time())
        run_object.properties = kwargs
        run_object.payload = {**initial_payload, **kwargs}
        return run_object.run()

    def run_debug_code(self, snippet_id=None, **kwargs):
        if not current_user.is_admin:
            return
        code = db.fetch("snippet", id=snippet_id).code if snippet_id else kwargs["code"]
        result = StringIO()
        with redirect_stdout(result):
            try:
                exec(
                    code,
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
        server = db.fetch("server", name=vs.server, rbac=None)
        if "application" not in server.allowed_automation:
            return {"error": "Runs from the UI are not allowed on this server."}
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
        kwargs["runtime"] = runtime = vs.get_time(randomize=True)
        run_name = kwargs.get("form", {}).get("name")
        if run_name and db.fetch("run", name=run_name, allow_none=True, rbac=None):
            return {"error": "There is already a run with the same name."}
        if kwargs.get("asynchronous", True):
            if vs.settings["automation"]["task_queue"] == "dramatiq":
                self.run.send(service_id, **kwargs)
            else:
                Thread(target=self.run, args=(service_id,), kwargs=kwargs).start()
        else:
            service.run(runtime=runtime)
        return {
            "service": service.to_dict(include_relations=["superworkflow"]),
            "runtime": runtime,
            "restart": "restart_runtime" in kwargs,
            "user": current_user.name,
        }

    def run_service_on_targets(self, **kwargs):
        return self.run_service(
            kwargs["service"],
            **{f"target_{kwargs['type']}s": kwargs["targets"].split("-")},
        )

    def save_file(self, id, **kwargs):
        file, content = db.fetch("file", id=id), None
        if kwargs.get("file_content"):
            with open(file.full_path, "w") as file:
                content = file.write(kwargs["file_content"])
        return content

    def save_positions(self, type, id, **kwargs):
        instance = db.fetch(type, allow_none=True, id=id, rbac="edit")
        if not instance:
            return
        relation_type = "device" if type == "network" else "service"
        id_to_name = {
            str(obj.id): obj.name
            for obj in db.fetch_all(relation_type, id_in=kwargs.keys())
        }
        for id, position in kwargs.items():
            new_position = [position["x"], position["y"]]
            if "-" not in id and id in id_to_name:
                instance.positions[id_to_name[id]] = new_position
            elif id in instance.labels:
                instance.labels[id] = {**instance.labels[id], "positions": new_position}
        instance.last_modified = vs.get_time()
        return instance.last_modified, instance.positions

    def save_profile(self, **kwargs):
        current_user.update(**kwargs)

    def save_settings(self, **kwargs):
        vs.settings = vs.template_context["settings"] = kwargs["settings"]
        if kwargs["save"]:
            with open(vs.path / "setup" / "settings.json", "w") as file:
                dump(kwargs["settings"], file, indent=2)

    def scan_folder(self, path=""):
        env.log("info", "Starting Scan of Files")
        path = f"{vs.file_path}{path.replace('>', '/')}"
        if not exists(path):
            return {"alert": "This folder does not exist on the filesystem."}
        elif not str(Path(path).resolve()).startswith(f"{vs.file_path}"):
            return {"error": "The path resolves outside of the files folder."}
        files_set = {
            file
            for file in db.session.query(vs.models["file"])
            .filter(vs.models["file"].full_path.startswith(path))
            .all()
        }
        for file in files_set:
            if exists(file.full_path):
                continue
            if vs.settings["files"]["delete_if_not_found"]:
                db.session.delete(file)
            else:
                file.status = "Not Found"
        file_path_set = {file.full_path for file in files_set}
        ignored_types = vs.settings["files"]["ignored_types"]
        creation_time = vs.get_time()
        insert_data, stack = defaultdict(list), [path]
        while stack:
            folder = stack.pop()
            with scandir(folder) as entries:
                for entry in entries:
                    if entry.is_dir():
                        stack.append(entry.path)
                    if entry.path in file_path_set:
                        continue
                    elif splitext(entry.name)[1] in ignored_types:
                        continue
                    scoped_path = entry.path.replace(str(vs.file_path), "")
                    stat_info = entry.stat()
                    last_modified = str(datetime.fromtimestamp(stat_info.st_mtime))
                    model = "folder" if entry.is_dir() else "generic_file"
                    insert_data[model].append(
                        {
                            "creation_time": creation_time,
                            "type": model,
                            "filename": entry.name,
                            "folder_path": folder,
                            "full_path": entry.path,
                            "last_modified": last_modified,
                            "name": scoped_path.replace("/", ">"),
                            "path": scoped_path,
                            "size": stat_info.st_size,
                        }
                    )
        for model, batch in insert_data.items():
            for batch in batched(batch, vs.database["transactions"]["batch_size"]):
                db.session.execute(insert(vs.models[model]), batch)
        env.log("info", "Scan of Files Successful")

    def scan_playbook_folder(self):
        playbooks = [
            [
                str(file).replace(str(vs.playbook_path), "")
                for file in Path(vs.playbook_path).glob(extension)
            ]
            for extension in ("*.yaml", "*.yml")
        ]
        return sorted(sum(playbooks, []))

    def scheduler_action(self, mode, **kwargs):
        for task in self.filtering("task", properties=["id"], form=kwargs):
            self.task_action(mode, task.id)

    def skip_services(self, workflow_id, service_ids):
        services = db.fetch_all("service", id_in=service_ids.split("-"))
        workflow = db.fetch("workflow", id=workflow_id, rbac="edit")
        workflow.check_restriction_to_owners("edit")
        skip = not all(service.skip.get(workflow.name) for service in services)
        for service in services:
            if skip:
                service.skip[workflow.name] = skip
            else:
                service.skip.pop(workflow.name, None)
        workflow.update_last_modified_properties()
        return {
            "skip": "skip" if skip else "unskip",
            "update_time": workflow.last_modified,
        }

    def stop_run(self, runtime):
        run = db.fetch("run", allow_none=True, rbac="run", runtime=runtime)
        if not run:
            return {"alert": "You don't have permission to stop this workflow."}
        elif run.status != "Running":
            return {"alert": "The service is not currently running."}
        elif env.redis_queue:
            env.redis("set", f"stop/{runtime}", "true")
        else:
            vs.run_stop[runtime] = True

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
                    if isinstance(value, bytes):
                        value = str(env.decrypt(value), "utf-8")
                    sheet.write(obj_index, index, str(value))
        workbook.save(vs.file_path / "spreadsheets" / filename)

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
                    db.factory(obj_type, **values)
                except Exception as exc:
                    info(f"{str(values)} could not be imported ({str(exc)})")
                    status = "Partial import (see logs)."
            db.session.commit()
        env.log("info", status)
        return status

    def update(self, type, **kwargs):
        try:
            kwargs["must_be_new"] = kwargs.get("id") == ""
            kwargs["update_source"] = "Edit Panel"
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
            instance = db.factory(type, commit=True, **kwargs)
            if hasattr(instance, "post_update"):
                instance.post_update()
            if kwargs.get("copy"):
                db.fetch(type, id=kwargs["copy"]).duplicate(clone=instance)
            if relations := vs.properties["update"].get(instance.class_type):
                return instance.to_dict(include_relations=relations)
            return instance.get_properties()
        except db.rbac_error:
            return {"alert": "Error 403 - Not Authorized."}
        except Exception as exc:
            db.session.rollback()
            if isinstance(exc, IntegrityError):
                return {"alert": f"There is already a {type} with the same parameters."}
            env.log("error", format_exc())
            return {"alert": str(exc)}

    def update_all_pools(self):
        for pool in db.fetch_all("pool", rbac="edit"):
            pool.compute_pool(commit=True)

    def update_database_configurations_from_git(self, force_update=False):
        path = vs.path / vs.automation["configuration_backup"]["folder"]
        env.log("info", f"Updating device configurations with data from {path}")
        for dir in scandir(path):
            user = "admin" if force_update else current_user.name
            device = db.fetch("device", allow_none=True, name=dir.name, user=user)
            timestamp_path = Path(dir.path) / "timestamps.json"
            if not device:
                continue
            try:
                with open(timestamp_path) as file:
                    timestamps = load(file)
            except Exception:
                timestamps = {}
            for property in vs.configuration_properties:
                no_update = False
                for timestamp, value in timestamps.get(property, {}).items():
                    if timestamp == "update":
                        db_date = getattr(device, f"last_{property}_update")
                        if db_date != "Never" and not force_update:
                            no_update = vs.str_to_date(value) <= vs.str_to_date(db_date)
                    setattr(device, f"last_{property}_{timestamp}", value)
                filepath = Path(dir.path) / property
                no_update = no_update and getattr(device, property)
                if not filepath.exists() or no_update:
                    continue
                with open(filepath) as file:
                    setattr(device, property, file.read())
            db.session.commit()
        for pool in db.fetch_all("pool", rbac=None):
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
                db.session.commit()

    def update_pool(self, pool_id):
        db.fetch("pool", id=int(pool_id), rbac="edit").compute_pool()

    def upload_files(self, **kwargs):
        path = f"{vs.file_path}/{kwargs['folder']}/{kwargs['file'].filename}"
        if not str(Path(path).resolve()).startswith(f"{vs.file_path}/"):
            return {"error": "The path resolves outside of the files folder."}
        kwargs["file"].save(path)

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
            "DEVICE": device.name,
            "ENDPOINT": endpoint,
            "ENMS_USER": getenv("ENMS_USER", "admin"),
            "ENMS_PASSWORD": getenv("ENMS_PASSWORD", "admin"),
            "FLASK_APP": "app.py",
            "IP_ADDRESS": getattr(device, kwargs["address"]),
            "OPTIONS": options,
            "PORT": str(device.port),
            "PROTOCOL": kwargs["protocol"],
            "REDIRECTION": str(vs.settings["ssh"]["port_redirection"]),
            "SERVER": vs.server,
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
