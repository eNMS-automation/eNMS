from base.database import db
from base.models import CustomBase
from sqlalchemy import Boolean, Column, Integer, String
try:
    from SocketServer import BaseRequestHandler, UDPServer
except Exception:
    from socketserver import BaseRequestHandler, UDPServer
from threading import Thread


class Log(CustomBase):

    __tablename__ = 'Log'

    id = Column(Integer, primary_key=True)
    source = Column(String)
    content = Column(String)
    visible = Column(Boolean, default=True)

    def __init__(self, source, content):
        self.source = source
        self.content = content


class SyslogUDPHandler(BaseRequestHandler):

    def handle(self):
        data = bytes.decode(self.request[0].strip())
        source, _ = self.client_address
        log = Log(source, str(data))
        db.session.add(log)
        db.session.commit()


class SyslogServer(CustomBase):

    __tablename__ = 'SyslogServer'

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(120))
    port = Column(Integer)

    def __init__(self, **kwargs):
        self.ip_address = str(kwargs['ip_address'][0])
        self.port = int(''.join(kwargs['port']))
        self.start()

    def __repr__(self):
        return self.ip_address

    def start(self):
        UDPServer.allow_reuse_address = True
        self.server = UDPServer((self.ip_address, self.port), SyslogUDPHandler)
        th = Thread(target=self.server.serve_forever)
        th.daemon = True
        th.start()
