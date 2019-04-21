from collections import Counter
from contextlib import contextmanager
from flask import Flask
from flask.wrappers import Response
from flask_login import current_user
from logging import info
from sqlalchemy import and_
from sqlalchemy.orm import Session
from typing import Generator

from eNMS.framework import (
    delete,
    delete_all,
    factory,
    fetch,
    fetch_all,
    fetch_all_visible,
    get,
    get_one,
    objectify,
    post,
)
from eNMS.models import classes, service_classes
from eNMS.modules import (
    bp,
    db,
    ldap_client,
    scheduler,
    tacacs_client,
    USE_LDAP,
    USE_TACACS,
)
from eNMS.properties import (
    cls_to_properties,
    default_diagrams_properties,
    google_earth_styles,
    link_subtype_to_color,
    pretty_names,
    private_properties,
    property_types,
    reverse_pretty_names,
    subtype_sizes,
    table_fixed_columns,
    table_properties,
    type_to_diagram_properties,
)


class Controller:
    def delete_instance(self, cls: str, instance_id: int) -> dict:
        instance = delete(cls, id=instance_id)
        info(f'{current_user.name}: DELETE {cls} {instance["name"]} ({id})')
        return instance

    def filtering(self, table: str, request: dict) -> dict:
        model = classes.get(table, classes["Device"])
        properties = table_properties[table]
        if table in ("configuration", "device"):
            properties.append("current_configuration")
        try:
            order_property = properties[int(request["order[0][column]"])]
        except IndexError:
            order_property = "name"
        order = getattr(getattr(model, order_property), request["order[0][dir]"])()
        constraints = []
        for property in properties:
            value = request.get(f"form[{property}]")
            if value:
                constraints.append(getattr(model, property).contains(value))
        result = db.session.query(model).filter(and_(*constraints)).order_by(order)
        if table in ("device", "link", "configuration"):
            pools = [int(id) for id in request.getlist("form[pools][]")]
            if pools:
                result = result.filter(model.pools.any(classes["pool"].id.in_(pools)))
        return {
            "draw": int(request["draw"]),
            "recordsTotal": len(model.query.all()),
            "recordsFiltered": len(result.all()),
            "data": [
                [getattr(obj, property) for property in properties]
                + obj.generate_row(table)
                for obj in result.limit(int(request["length"]))
                .offset(int(request["start"]))
                .all()
            ],
        }

    def get_cluster_status(self) -> dict:
        return {
            attr: [getattr(instance, attr) for instance in fetch_all("Instance")]
            for attr in ("status", "cpu_load")
        }

    def get_counters(self, property: str, type: str) -> Counter:
        property = reverse_pretty_names.get(property, property)
        return Counter(str(getattr(instance, property)) for instance in fetch_all(type))

    def init_app(self, app: Flask, session: Session):
        self.app = app
        self.session = session

    def object_import(self, request: dict, file: FileStorage) -> str:
        if request["replace"]:
            delete_all("Device")
        result = "Topology successfully imported."
        if allowed_file(secure_filename(file.filename), {"xls", "xlsx"}):
            book = open_workbook(file_contents=file.read())
            for obj_type in ("Device", "Link"):
                try:
                    sheet = book.sheet_by_name(obj_type)
                except XLRDError:
                    continue
                properties = sheet.row_values(0)
                for row_index in range(1, sheet.nrows):
                    values = dict(zip(properties, sheet.row_values(row_index)))
                    values["dont_update_pools"] = True
                    try:
                        factory(obj_type, **values).serialized
                    except Exception as e:
                        info(f"{str(values)} could not be imported ({str(e)})")
                        result = "Partial import (see logs)."
                db.session.commit()
        for pool in fetch_all("Pool"):
            pool.compute_pool()
        db.session.commit()
        info("Inventory import: Done.")
        return result

    def object_export(self, request: dict, path_app: PosixPath) -> bool:
        workbook = Workbook()
        filename = request["export_filename"]
        if "." not in filename:
            filename += ".xls"
        for obj_type in ("Device", "Link"):
            sheet = workbook.add_sheet(obj_type)
            for index, property in enumerate(export_properties[obj_type]):
                sheet.write(0, index, property)
                for obj_index, obj in enumerate(fetch_all(obj_type), 1):
                    sheet.write(obj_index, index, getattr(obj, property))
        workbook.save(path_app / "projects" / filename)
        return True

    @contextmanager
    def session_scope() -> Generator:
        session = self.session()  # type: ignore
        try:
            yield session
            session.commit()
        except Exception as e:
            info(str(e))
            session.rollback()
            raise e
        finally:
            self.session.remove()


controller = Controller()
