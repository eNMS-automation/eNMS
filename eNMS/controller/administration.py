from collections import defaultdict
from contextlib import redirect_stdout
from datetime import datetime
from difflib import unified_diff
from flask_login import current_user
from git import Repo
from io import StringIO
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

from eNMS import app
from eNMS.database import db
from eNMS.models import models, model_properties, relationships


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

    def database_deletion(self, **kwargs):
        db.delete_all(*kwargs["deletion_types"])

    def delete_file(self, filepath):
        remove(Path(filepath.replace(">", "/")))

    def delete_instance(self, model, instance_id):
        return db.delete(model, id=instance_id)

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

    def get_properties(self, model, id):
        return db.fetch(model, id=id).get_properties()

    def get_session_log(self, session_id):
        return db.fetch("session", id=session_id).content

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

    def run_debug_code(self, **kwargs):
        result = StringIO()
        with redirect_stdout(result):
            try:
                environment = {"app": self, "db": db, "models": models}
                exec(kwargs["code"], environment)
            except Exception:
                return format_exc()
        return result.getvalue()

    def save_file(self, filepath, **kwargs):
        if kwargs.get("file_content"):
            with open(Path(filepath.replace(">", "/")), "w") as file:
                return file.write(kwargs["file_content"])

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

    def switch_menu(self, user_id):
        user = db.fetch("user", rbac=None, id=user_id)
        user.small_menu = not user.small_menu

    def switch_theme(self, user_id, theme):
        db.fetch("user", rbac=None, id=user_id).theme = theme

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
