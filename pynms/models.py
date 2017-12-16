from collections import OrderedDict
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from main import db, scheduler
from database import Base

class CustomBase(Base):
    
    __abstract__ = True
    
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if property in self.__table__.columns._data:
                # depending on whether value is an iterable or not, we must
                # unpack it's value (when **kwargs is request.form, some values
                # will be a 1-element list)
                if hasattr(value, '__iter__') and not isinstance(value, str):
                    value ,= value
                setattr(self, property, value)
    
    # simplifies the syntax for flask forms
    @classmethod
    def choices(cls):
        print(cls)
        return [(obj, obj) for obj in cls.query.all()]
