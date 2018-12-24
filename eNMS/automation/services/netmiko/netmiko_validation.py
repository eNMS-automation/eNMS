from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from eNMS.automation.helpers import NETMIKO_DRIVERS
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class NetmikoValidationService(Service):

    __tablename__ = 'NetmikoValidationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    command = Column(String)
    content_match = Column(String)
    content_match_textarea = True
    content_match_regex = Column(Boolean)
    negative_logic = Column(Boolean)
    delete_spaces_before_matching = Column(Boolean)
    driver = Column(String)
    driver_values = NETMIKO_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.)
    global_delay_factor = Column(Float, default=1.)

    __mapper_args__ = {
        'polymorphic_identity': 'NetmikoValidationService',
    }

    def job(self, device, _):
        netmiko_handler = self.netmiko_connection(device)
        command = self.sub(self.command, locals())
        result = netmiko_handler.send_command(command)
        match = self.sub(self.content_match, locals())
        netmiko_handler.disconnect()
        return {
            'expected': match,
            'negative_logic': self.negative_logic,
            'result': result,
            'success': self.match_content(result, match)
        }


service_classes['NetmikoValidationService'] = NetmikoValidationService
