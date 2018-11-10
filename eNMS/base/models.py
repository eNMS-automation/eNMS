from flask_wtf import FlaskForm
from json import dumps, loads

from eNMS import db, use_vault, vault_client
from eNMS.base.helpers import fetch, objectify, choices
from eNMS.base.properties import (
    cls_to_properties,
    property_types,
    boolean_properties,
    relationships as rel,
    private_properties
)


class Base(db.Model):

    __abstract__ = True

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def __lt__(self, other):
        return True

    def __repr__(self):
        return self.name

    def __getattribute__(self, property):
        if property in private_properties and use_vault:
            path = f'secret/data/{self.type}/{self.name}/{property}'
            return vault_client.read(path)['data']['data'][property]
        else:
            return super().__getattribute__(property)

    def __setattr__(self, property, value):
        if property in private_properties:
            if not value:
                return
            if use_vault:
                vault_client.write(
                    f'secret/data/{self.type}/{self.name}/{property}',
                    data={property: value}
                )
        super().__setattr__(property, value)

    def update(self, **kwargs):
        serial = rel.get(self.__tablename__, rel['Service'])
        for property, value in kwargs.items():
            property_type = property_types.get(property, None)
            if property in serial:
                value = fetch(serial[property], id=value)
            elif property[:-1] in serial:
                value = objectify(serial[property[:-1]], value)
            elif property in boolean_properties:
                value = kwargs[property] != 'off'
            elif 'regex' in property:
                value = property in kwargs
            elif property_type == 'dict':
                value = loads(value) if value else {}
            elif property_type in ['float', 'int']:
                value = {'float': float, 'int': int}[property_type](value or 0)
            setattr(self, property, value)

    @property
    def properties(self):
        class_name, result = self.__tablename__, {}
        for property in cls_to_properties[class_name]:
            try:
                dumps(getattr(self, property))
                result[property] = getattr(self, property)
            except TypeError:
                result[property] = str(getattr(self, property))
        return result

    def to_dict(self, export=False):
        get = 'id' if export else 'properties'
        properties = self.properties
        for property in rel.get(self.__tablename__, rel['Service']):
            if hasattr(self, property):
                if hasattr(getattr(self, property), 'properties'):
                    properties[property] = getattr(getattr(self, property), get)
            if hasattr(self, f'{property}s'):
                # a workflow has edges: we need to know not only the edge
                # properties, but also the properties of its source and
                # destination: we need the serialized edge.
                properties[f'{property}s'] = [
                    getattr(obj, get) for obj in getattr(self, f'{property}s')
                ]
        return properties

    @property
    def serialized(self):
        return self.to_dict()

    @property
    def visible(self):
        return not (hasattr(self, 'hidden') and self.hidden)

    @classmethod
    def export(cls):
        return [obj.to_dict(export=True) for obj in cls.query.all()]

    @classmethod
    def choices(cls):
        return [(obj.id, obj.name) for obj in cls.query.all() if obj.visible]

    @classmethod
    def serialize(cls):
        return [obj.serialized for obj in cls.query.all() if obj.visible]


class BaseForm(FlaskForm):

    def __init__(self, request, model=None):
        super().__init__(request)
        for property, cls in rel.get(model, {}).items():
            for name in (property.lower(), f'{property.lower()}s'):
                if hasattr(self, name):
                    getattr(self, name).choices = choices(cls)
