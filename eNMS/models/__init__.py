classes = {}
service_classes = {}


def register_class(*args, **kwargs):
    cls = type(*args, **kwargs)
    model = {cls.__tablename__: cls, cls.__tablename__.lower(): cls}
    if classes.get("Service") and issubclass(cls, classes["Service"]):
        service_classes.update(model)
    classes.update(model)
    return cls
