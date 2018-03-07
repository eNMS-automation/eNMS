from .database import Base


class CustomBase(Base):

    __abstract__ = True

    # simplifies the syntax for flask forms
    @classmethod
    def choices(cls):
        return [(obj, obj) for obj in cls.query.all()]

    def __repr__(self):
        return self.name

    # the visible classmethod is here because it can apply to both objects and logs
    @classmethod
    def visible_objects(cls):
        return (obj for obj in cls.query.all() if obj.visible)
