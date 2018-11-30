from re import search
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from socketserver import BaseRequestHandler, UDPServer
from threading import Thread

from eNMS import db, scheduler
from eNMS.base.associations import job_log_rule_table
from eNMS.base.models import Base


class Log(Base):

    __tablename__ = type = 'Log'
    id = Column(Integer, primary_key=True)
    source = Column(String)
    content = Column(String)
    log_rule_id = Column(Integer, ForeignKey('User.id'))
    user = relationship('User', back_populates='jobs')
    

    def __init__(self, source, content):
        self.source = source
        self.content = content


    def __repr__(self):
        return self.content


class LogRule(Base):

    __tablename__ = type = 'LogRule'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    source = Column(String)
    sourceregex = Column(Boolean)
    content = Column(String)
    contentregex = Column(Boolean)
    jobs = relationship(
        'Job',
        secondary=job_log_rule_table,
        back_populates='log_rules'
    )


class SyslogUDPHandler(BaseRequestHandler):

    def handle(self):
        print(self.request[0])
        with scheduler.app.app_context():
            data = str(bytes.decode(self.request[0].strip()))
            source, _ = self.client_address
            log_rules = []
            for log_rule in LogRule.query.all():
                source_match = (
                    search(log_rule.source, source) if log_rule.source_regex
                    else log_rule.source in source
                )
                content_match = (
                    search(log_rule.content, data) if log_rule.content_regex
                    else log_rule.content in data
                )
                if source_match and content_match:
                    log_rules.append(log_rule)
                    for job in log_rule.jobs:
                        job.try_run()
            log = Log(source, data, log_rules)
            db.session.add(log)
            db.session.commit()


class SyslogServer(Base):

    __tablename__ = type = 'SyslogServer'
    id = Column(Integer, primary_key=True)
    ip_address = Column(String)
    port = Column(Integer)

    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port
        self.start()

    def __repr__(self):
        return self.ip_address

    def start(self):
        UDPServer.allow_reuse_address = True
        self.server = UDPServer((self.ip_address, self.port), SyslogUDPHandler)
        th = Thread(target=self.server.serve_forever)
        th.daemon = True
        th.start()
