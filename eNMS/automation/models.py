from copy import deepcopy
from datetime import datetime
from json import load
from logging import info
from multiprocessing.pool import ThreadPool
from napalm import get_network_driver
from napalm.base.base import NetworkDriver
from netmiko import ConnectHandler
from os import environ
from paramiko import SSHClient
from re import compile, search
from scp import SCPClient
from sqlalchemy import Boolean, case, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import backref, relationship
from time import sleep
from traceback import format_exc
from typing import Any, List, Optional, Set, Tuple
from xmltodict import parse

from eNMS import db
from eNMS.associations import (
    job_device_table,
    job_log_rule_table,
    job_pool_table,
    job_workflow_table,
    log_rule_log_table,
)
from eNMS.extensions import controller
from eNMS.functions import fetch, session_scope
from eNMS.models.base_models import Base
