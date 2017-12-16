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
        
    def __repr__(self):
        return str(self.username)
