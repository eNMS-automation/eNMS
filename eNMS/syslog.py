from re import search
from socketserver import BaseRequestHandler, UDPServer
from threading import Thread

from eNMS.database import Session
from eNMS.database.functions import factory, fetch_all


class SyslogServer:
    def __init__(self, ip_address: str, port: int) -> None:
        self.ip_address = ip_address
        self.port = port
        self.start()

    def start(self) -> None:
        UDPServer.allow_reuse_address = True
        self.server = UDPServer((self.ip_address, self.port), SyslogUDPHandler)
        th = Thread(target=self.server.serve_forever)
        th.daemon = True
        th.start()


class SyslogUDPHandler(BaseRequestHandler):
    def handle(self) -> None:
        data = str(bytes.decode(self.request[0].strip()))
        source, _ = self.client_address
        events = []
        for event in fetch_all("Event"):
            source_match = (
                search(event.origin, source)
                if event.source_ip_regex
                else event.origin in source
            )
            content_match = (
                search(event.name, data) if event.content_regex else event.name in data
            )
            if source_match and content_match:
                events.append(event)
                for job in event.jobs:
                    job.try_run()
        if events:
            log = factory("Log", **{"source": source, "date": data, "events": events})
            Session.add(log)
            Session.commit()
