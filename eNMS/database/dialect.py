from os import environ
from sqlalchemy import PickleType, String, Text
from sqlalchemy.dialects.mysql.base import MSMediumBlob
from sqlalchemy.ext.mutable import MutableDict, MutableList

from eNMS.database import DIALECT


class CustomPickleType(PickleType):
    if DIALECT == "mysql":
        impl = MSMediumBlob


MutableDict = MutableDict.as_mutable(CustomPickleType)
MutableList = MutableList.as_mutable(CustomPickleType)
LargeString = Text(int(environ.get("LARGE_STRING_LENGTH", 2 ** 15)))
SmallString = String(int(environ.get("SMALL_STRING_LENGTH", 255)))
