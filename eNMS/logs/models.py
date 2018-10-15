from re import search
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from eNMS.base.associations import job_log_rule_table
from eNMS.base.custom_base import CustomBase


class SyslogUDPHandler(BaseRequestHandler):

    def handle(self):
        with scheduler.app.app_context():
            data = bytes.decode(self.request[0].strip())
            source, _ = self.client_address
            log = Log(source, str(data))
            db.session.add(log)
            db.session.commit()


class SyslogServer(CustomBase):

    __tablename__ = 'SyslogServer'

    id = Column(Integer, primary_key=True)
    ip_address = Column(String)
    port = Column(Integer)

    def __init__(self, **kwargs):
        self.ip_address = kwargs['ip_address']
        self.port = int(kwargs['port'])
        self.start()

    def __repr__(self):
        return self.ip_address

    def start(self):
        UDPServer.allow_reuse_address = True
        self.server = UDPServer((self.ip_address, self.port), SyslogUDPHandler)
        th = Thread(target=self.server.serve_forever)
        th.daemon = True
        th.start()


class Log(CustomBase):

    __tablename__ = 'Log'

    id = Column(Integer, primary_key=True)
    source = Column(String)
    content = Column(String)

    def __init__(self, source, content):
        self.source = source
        self.content = content
        for log_rule in LogRule.query.all():
            trigger_jobs = all(
                getattr(log_rule, prop) in getattr(self, prop)
                if not getattr(log_rule, prop + 'regex')
                else search(getattr(log_rule, prop), getattr(self, prop))
                for prop in ('source', 'content') if getattr(log_rule, prop)
            )
            if trigger_jobs:
                for job in log_rule.jobs:
                    job.run()

    def __repr__(self):
        return self.content


class LogRule(CustomBase):

    __tablename__ = 'LogRule'

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

    def __repr__(self):
        return self.content
