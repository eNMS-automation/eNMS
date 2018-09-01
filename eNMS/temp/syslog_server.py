try:
    from SocketServer import BaseRequestHandler, UDPServer
except Exception:
    from socketserver import BaseRequestHandler, UDPServer
from threading import Thread

class SyslogServer():


    def __init__(self):
        self.ip_address = '0.0.0.0'
        self.port = 514
        self.start()

    def __repr__(self):
        return self.ip_address

    def start(self):
        UDPServer.allow_reuse_address = True
        self.server = UDPServer((self.ip_address, self.port), SyslogUDPHandler)
        self.server.serve_forever()


class SyslogUDPHandler(BaseRequestHandler):

    def handle(self):
        data = bytes.decode(self.request[0].strip())
        print(data)
        source, _ = self.client_address

server = SyslogServer()
server.start()