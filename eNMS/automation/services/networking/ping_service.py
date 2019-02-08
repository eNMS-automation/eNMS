from subprocess import check_output
from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class PingService(Service):

    __tablename__ = 'PingService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    count = Column(String)
    timeout = Column(String)
    ttl = Column(String)
    packetsize = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'PingService',
    }

    def job(self, device, _):
        command = 'ping -c {} -W {} -t {} -s {} {}'.format(
            self.count,
            self.timeout,
            self.ttl,
            self.packetsize,
            device.ip_address
        ).split(' ')
        try:
            output = check_output(command).decode().strip().splitlines()
            total = output[-2].split(',')[3].split()[1]
            loss = output[-2].split(',')[2].split()[0]
            timing = output[-1].split()[3].split('/')
            return {
                'success': True,
                'result': {
                    'probes_sent': self.count,
                    'packet_loss': loss,
                    'rtt_min': timing[0],
                    'rtt_max': timing[2],
                    'rtt_avg': timing[1],
                    'rtt_stddev': timing[3],
                    'total rtt': total
                }
            }
        except Exception as e:
            return {
                'success': False,
                'result': str(e)
            }


service_classes['PingService'] = PingService
