from socket import error, gaierror, socket, timeout
from subprocess import run as sub_run
from sqlalchemy import ForeignKey, Integer

from eNMS.database import db
from eNMS.forms import ServiceForm
from eNMS.fields import HiddenField, IntegerField, SelectField, StringField
from eNMS.models.automation import Service


class PingService(Service):

    __tablename__ = "ping_service"
    pretty_name = "ICMP / TCP Ping"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    protocol = db.Column(db.SmallString)
    ip_address = db.Column(db.SmallString)
    ports = db.Column(db.SmallString)
    count = db.Column(Integer, default=5)
    timeout = db.Column(Integer, default=2)
    ttl = db.Column(Integer, default=60)
    packet_size = db.Column(Integer, default=56)

    __mapper_args__ = {"polymorphic_identity": "ping_service"}

    def job(self, run, device=None):
        ip_address = run.sub(run.ip_address, locals()) or device.ip_address
        if run.protocol == "ICMP":
            command = ["ping"]
            for variable, property in (
                ("c", "count"),
                ("W", "timeout"),
                ("t", "ttl"),
                ("s", "packet_size"),
            ):
                value = getattr(self, property)
                if value:
                    command.extend(f"-{variable} {value}".split())
            command.append(ip_address)
            run.log("info", f"Running PING ({command})", device)
            sub_result, result = sub_run(command, capture_output=True), None
            output = sub_result.stdout.decode().strip().splitlines()
            if sub_result.returncode == 0:
                # The first ping statistics line can look like either:
                # - 3 packets transmitted, 0 received, +3 errors,
                # 100% packet loss, time 2055ms
                # - 3 packets transmitted, 0 received, 100% packet loss, time 2081ms
                error_offset = 1 if "errors," in output[-2] else 0
                sent = output[-2].split(",")[0].split()[0].strip()
                rcvd = output[-2].split(",")[1].split()[0].strip()
                if error_offset:
                    errors = output[-2].split(",")[2].split()[0].strip()
                else:
                    errors = 0
                total = output[-2].split(",")[3 + error_offset].split()[1].strip()
                loss = output[-2].split(",")[2 + error_offset].split()[0].strip()
                timing = output[-1].split()[3].split("/")
                result = {
                    "probes_sent": sent,
                    "probes_rcvd": rcvd,
                    "errors": errors,
                    "packet_loss": loss,
                    "rtt_min": timing[0],
                    "rtt_max": timing[2],
                    "rtt_avg": timing[1],
                    "rtt_stddev": timing[3],
                    "total rtt": total,
                }
            return {
                "error": sub_result.stderr.decode().strip(),
                "output": "\n".join(output),
                "result": result,
                "success": sub_result.returncode == 0,
            }
        else:
            result = {}
            for port in map(int, run.ports.split(",")):
                s = socket()
                s.settimeout(run.timeout)
                try:
                    connection = not s.connect_ex((ip_address, port))
                except (gaierror, timeout, error):
                    connection = False
                finally:
                    s.close()
                result[port] = connection
            return {"success": all(result.values()), "result": result}


class PingForm(ServiceForm):
    form_type = HiddenField(default="ping_service")
    protocol = SelectField(choices=(("ICMP", "ICMP Ping"), ("TCP", "TCP Ping")))
    ip_address = StringField("IP Address", substitution=True, help="ping/ip_address")
    ports = StringField("Ports (TCP ping only)", default=22)
    count = IntegerField(default=5)
    timeout = IntegerField(default=2)
    ttl = IntegerField(default=60)
    packet_size = IntegerField(default=56)

    def validate(self):
        valid_form = super().validate()
        invalid_tcp_port = self.protocol.data == "TCP" and not self.ports.data
        if invalid_tcp_port:
            self.ports.errors.append("You must enter a port for a TCP ping.")
        return valid_form and not invalid_tcp_port
