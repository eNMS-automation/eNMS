from socketserver import BaseRequestHandler, UDPServer
from threading import Thread

from eNMS.database import db


class SyslogServer:
    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port
        self.start()

    def start(self):
        UDPServer.allow_reuse_address = True
        self.server = UDPServer((self.ip_address, self.port), SyslogUDPHandler)
        th = Thread(target=self.server.serve_forever)
        th.daemon = True
        th.start()


class SyslogUDPHandler(BaseRequestHandler):
    def handle(self):
        address = self.client_address[0]
        device = db.fetch("device", allow_none=True, ip_address=address)
        properties = {
            "source": device.name if device else address,
            "content": str(bytes.decode(self.request[0].strip())),
        }
        for event in db.fetch_all("event"):
            event.match_log(**properties)
