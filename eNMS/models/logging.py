from datetime import datetime
from re import search
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from socketserver import BaseRequestHandler, UDPServer
from threading import Thread
from typing import List

from eNMS.controller import controller
from eNMS.database import Session, SMALL_STRING_LENGTH, LARGE_STRING_LENGTH
from eNMS.models.associations import job_log_rule_table, log_rule_log_table
from eNMS.database.base import AbstractBase


class Log(AbstractBase):

    __tablename__ = type = "Log"
    id = Column(Integer, primary_key=True)
    origin = Column(String(SMALL_STRING_LENGTH), default="")
    severity = Column(String(SMALL_STRING_LENGTH), default="N/A")
    content = Column(String(LARGE_STRING_LENGTH), default="")
    time = Column(String(SMALL_STRING_LENGTH), default="")
    log_rules = relationship(
        "LogRule", secondary=log_rule_log_table, back_populates="logs"
    )

    def update(self, **kwargs: str) -> None:
        kwargs["time"] = str(datetime.now())
        super().update(**kwargs)

    def generate_row(self, table: str) -> List[str]:
        return []


class LogRule(AbstractBase):

    __tablename__ = type = "LogRule"
    id = Column(Integer, primary_key=True)
    name = Column(String(SMALL_STRING_LENGTH), unique=True)
    origin = Column(String(SMALL_STRING_LENGTH), default="")
    origin_regex = Column(Boolean, default=False)
    name = Column(String(SMALL_STRING_LENGTH), default="")
    content_regex = Column(Boolean, default=False)
    logs = relationship("Log", secondary=log_rule_log_table, back_populates="log_rules")
    jobs = relationship("Job", secondary=job_log_rule_table, back_populates="log_rules")

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showTypePanel('logrule', '{self.id}')">
            Edit</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="deleteInstance('logrule', '{self.id}', '{self.name}')">
            Delete</button>""",
        ]


class SyslogServer(AbstractBase):

    __tablename__ = type = "SyslogServer"
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(SMALL_STRING_LENGTH))
    port = Column(Integer)

    def __init__(self, ip_address: str, port: int) -> None:
        self.ip_address = ip_address
        self.port = port
        self.start()

    def __repr__(self) -> str:
        return self.ip_address

    def start(self) -> None:
        UDPServer.allow_reuse_address = True
        self.server = UDPServer((self.ip_address, self.port), SyslogUDPHandler)
        th = Thread(target=self.server.serve_forever)
        th.daemon = True
        th.start()


class SyslogUDPHandler(BaseRequestHandler):
    def handle(self) -> None:
        with controller.app.app_context():
            data = str(bytes.decode(self.request[0].strip()))
            source, _ = self.client_address
            log_rules = []
            for log_rule in Session.query(LogRule).all():
                source_match = (
                    search(log_rule.origin, source)
                    if log_rule.source_ip_regex
                    else log_rule.origin in source
                )
                content_match = (
                    search(log_rule.name, data)
                    if log_rule.content_regex
                    else log_rule.name in data
                )
                if source_match and content_match:
                    log_rules.append(log_rule)
                    for job in log_rule.jobs:
                        job.try_run()
            if log_rules:
                log = Log(**{"source": source, "date": data, "log_rules": log_rules})
                Session.add(log)
                Session.commit()
