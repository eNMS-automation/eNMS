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
    for col in cls.__table__.columns:
        cls_to_properties[cls.type].append(col.key)
        if issubclass(cls, classes["Service"]):
            service_import_properties.append(col.key)
        if col.type == PickleType and col.default.arg == []:
            property_types[col.key] = "list"
        else:
            property_types[col.key] = {
                Boolean: "bool",
                Integer: "int",
                Float: "float",
                PickleType: "dict",
            }.get(type(col.type), "str")
    model = {cls.__tablename__: cls, cls.__tablename__.lower(): cls}
    if classes.get("Service") and issubclass(cls, classes["Service"]):
        service_classes.update(model)
    classes.update(model)
    return cls
