from eNMS import db
from eNMS.base.properties import cls_to_properties


class CustomBase(db.Model):

    __abstract__ = True

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def __repr__(self):
        return self.name

    def __lt__(self, other):
        return True

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def serialized(self):
        return {
            p: getattr(self, p) for p in cls_to_properties[self.__tablename__]
        }

    @classmethod
    def choices(cls):
        return [(obj.id, obj.name) for obj in cls.query.all()]

    @classmethod
    def serialize(cls):
        return [obj.serialized for obj in cls.query.all()]
