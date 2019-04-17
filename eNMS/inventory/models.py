from re import search
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    PickleType,
    String,
    Text,
    Float,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import backref, relationship
from typing import Any, Dict, List, Union

from eNMS.associations import (
    pool_device_table,
    pool_link_table,
    pool_user_table,
    job_device_table,
    job_pool_table,
)

from eNMS.models.base_models import Base
from eNMS.properties import (
    custom_properties,
    pool_link_properties,
    pool_device_properties,
    sql_types,
)
