from socketserver import BaseRequestHandler, UDPServer
from threading import Thread


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
