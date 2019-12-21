from flask_login import UserMixin
from sqlalchemy import Boolean, Float, Integer
from sqlalchemy.orm import relationship

from eNMS.database.dialect import Column, MutableList, SmallString
from eNMS.database.associations import pool_user_table
from eNMS.database.base import AbstractBase


class Server(AbstractBase):

    __tablename__ = type = "server"
    id = Column(Integer, primary_key=True)
    name = Column(SmallString, unique=True)
    description = Column(SmallString)
    ip_address = Column(SmallString)
    weight = Column(Integer, default=1)
    status = Column(SmallString, default="down")
    cpu_load = Column(Float)


class User(AbstractBase, UserMixin):

    __tablename__ = type = "user"
    id = Column(Integer, primary_key=True)
    email = Column(SmallString)
    name = Column(SmallString)
    permissions = Column(MutableList)
    pools = relationship("Pool", secondary=pool_user_table, back_populates="users")
    password = Column(SmallString)
    small_menu = Column(Boolean, default=False)

    @property
    def is_admin(self):
        return "Admin" in self.permissions

    def allowed(self, permission):
        return self.is_admin or permission in self.permissions
