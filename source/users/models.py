from flask_login import UserMixin
from sqlalchemy import Column, Integer, String
from base.models import CustomBase

class User(CustomBase, UserMixin):
    
    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    username = Column(String(120), unique=True)
    email = Column(String(120), unique=True)
    access_rights = Column(String(120))
    password = Column(String(30))
    secret_password = Column(String(30))
    dashboard_node_properties = Column(String())
    dashboard_link_properties = Column(String())

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value ,= value
            setattr(self, property, value)
        self.dashboard_node_properties = str(['type'])
        self.dashboard_link_properties = str(['type'])
        
    def __repr__(self):
        return str(self.username)
