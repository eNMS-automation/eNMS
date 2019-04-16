from re import search
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from socketserver import BaseRequestHandler, UDPServer
from threading import Thread
from typing import List

from eNMS.extensions import controller, db
from eNMS.associations import job_log_rule_table, log_rule_log_table
from eNMS.models import Base


class Log(Base):

    __tablename__ = type = "Log"
    id = Column(Integer, primary_key=True)
    source_ip = Column(String(255))
    content = Column(String(255))
    log_rules = relationship(
        "LogRule", secondary=log_rule_log_table, back_populates="logs"
    )

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="deleteInstance('Log', '{self.id}')">Delete</button>"""
        ]

    def __repr__(self) -> str:
        return self.content


class LogRule(Base):

    __tablename__ = type = "LogRule"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    source_ip = Column(String(255))
    source_ip_regex = Column(Boolean)
    content = Column(String(255))
    content_regex = Column(Boolean)
    logs = relationship("Log", secondary=log_rule_log_table, back_populates="log_rules")
    jobs = relationship("Job", secondary=job_log_rule_table, back_populates="log_rules")

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showTypeModal('logrule', '{self.id}')">
            Edit</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="deleteInstance('logrule', '{self.id}')">
            Delete</button>""",
        ]


class SyslogUDPHandler(BaseRequestHandler):
    def handle(self) -> None:
        with controller.app.app_context():
            data = str(bytes.decode(self.request[0].strip()))
            source, _ = self.client_address
            log_rules = []
            for log_rule in LogRule.query.all():
                source_match = (
                    search(log_rule.source_ip, source)
                    if log_rule.source_ip_regex
                    else log_rule.source_ip in source
                )
                content_match = (
                    search(log_rule.content, data)
                    if log_rule.content_regex
                    else log_rule.content in data
                )
                if source_match and content_match:
                    log_rules.append(log_rule)
                    for job in log_rule.jobs:
                        job.try_run()
            if log_rules:
                log = Log(**{"source": source, "date": data, "log_rules": log_rules})
                db.session.add(log)
                db.session.commit()


class SyslogServer(Base):

    __tablename__ = type = "SyslogServer"
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(255))
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
