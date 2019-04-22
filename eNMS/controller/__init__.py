from collections import Counter
from contextlib import contextmanager
from flask import Flask
from flask.wrappers import Response
from flask_login import current_user
from logging import info
from pathlib import Path, PosixPath
from sqlalchemy import and_
from sqlalchemy.orm import Session
from typing import Generator, Set
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

from eNMS.controller.automation_controller import AutomationController
from eNMS.controller.import_export_controller import ImportExportController
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


class Controller(AutomationController, ImportExportController):
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

    def init_app(self, app: Flask, session: Session):
        self.app = app
        self.session = session

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
