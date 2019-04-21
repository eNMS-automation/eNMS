classes = {}
service_classes = {}


def register_class(*args, **kwargs):
    cls = type(*args, **kwargs)
    if classes.get("Service") and issubclass(cls, classes["Service"]):
        service_classes[cls.__tablename__] = cls
    classes[cls.__tablename__] = cls
    return cls
