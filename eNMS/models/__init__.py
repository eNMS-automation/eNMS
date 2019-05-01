from collections import defaultdict
from sqlalchemy import Boolean, Float, Integer, PickleType, String
from typing import Dict

from eNMS.properties import service_import_properties

classes = {}
service_classes = {}

cls_to_properties = defaultdict(list)
property_types: Dict[str, str] = {}


def register_class(*args, **kwargs):
    cls = type(*args, **kwargs)
    is_service = classes.get("Service") and issubclass(cls, classes["Service"])
    for col in cls.__table__.columns:
        cls_to_properties[cls.__tablename__].append(col.key)
        if is_service:
            service_import_properties.append(col.key)
        if col.type == PickleType and col.default.arg == []:
            property_types[col.key] = "list"
        else:
            column_type = {
                Boolean: "bool",
                Integer: "int",
                Float: "float",
                PickleType: "dict",
            }.get(type(col.type), "str")
            if col.key not in property_types:
                property_types[col.key] = column_type
    if hasattr(cls, "parent_cls"):
        cls_to_properties[cls.__tablename__].extend(cls_to_properties[cls.parent_cls])
    model = {cls.__tablename__: cls, cls.__tablename__.lower(): cls}
    if is_service:
        service_classes.update(model)
    classes.update(model)
    return cls
