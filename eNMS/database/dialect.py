from os import environ
from sqlalchemy import Column as SQLA_Column, PickleType, String, Text
from sqlalchemy.dialects.mysql.base import MSMediumBlob
from sqlalchemy.ext.mutable import MutableDict, MutableList

from eNMS.controller import config
from eNMS.database import DIALECT


class CustomPickleType(PickleType):
    if DIALECT == "mysql":
        impl = MSMediumBlob


MutableDict = MutableDict.as_mutable(CustomPickleType)
MutableList = MutableList.as_mutable(CustomPickleType)
LargeString = Text(config["database"]["large_string_length"])
SmallString = String(config["database"]["small_string_length"])


default_ctypes = {
    MutableDict: {},
    MutableList: [],
    LargeString: "",
    SmallString: "",
    Text: "",
}


class Column(SQLA_Column):
    def __init__(self, ctype, *args, **kwargs):
        if "default" not in kwargs and ctype in default_ctypes:
            kwargs["default"] = default_ctypes[ctype]
        super().__init__(ctype, *args, **kwargs)
