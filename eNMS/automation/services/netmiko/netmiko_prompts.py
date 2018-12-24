from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from eNMS.automation.helpers import NETMIKO_DRIVERS
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class NetmikoPromptsService(Service):

    __tablename__ = 'NetmikoPromptsService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    command = Column(String)
    confirmation1 = Column(String)
    response1 = Column(String)
    confirmation2 = Column(String)
    response2 = Column(String)
    confirmation3 = Column(String)
    response3 = Column(String)
    content_match = Column(String)
    content_match_textarea = True
    content_match_regex = Column(Boolean)
    delay_factor = Column(Float, default=2.)
    negative_logic = Column(Boolean)
    delete_spaces_before_matching = Column(Boolean)
    driver = Column(String)
    driver_values = NETMIKO_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.)
    global_delay_factor = Column(Float, default=1.)

    __mapper_args__ = {
        'polymorphic_identity': 'NetmikoPromptsService',
    }

    def job(self, device, _):
        netmiko_handler = self.netmiko_connection(device)
        command = self.sub(self.command, locals())
        result = netmiko_handler.send_command_timing(command, delay_factor=2)
        if self.response1 and self.confirmation1 in result:
            result = netmiko_handler.send_command_timing(
                self.response1,
                delay_factor=self.delay_factor
            )
            if self.response2 and self.confirmation2 in result:
                result = netmiko_handler.send_command_timing(
                    self.response2,
                    delay_factor=self.delay_factor
                )
                if self.response3 and self.confirmation3 in result:
                    result = netmiko_handler.send_command_timing(
                        self.response3,
                        delay_factor=self.delay_factor
                    )
        match = self.sub(self.content_match, locals())
        netmiko_handler.disconnect()
        return {
            'expected': match,
            'negative_logic': self.negative_logic,
            'result': result,
            'success': self.match_content(result, match)
        }


service_classes['NetmikoPromptsService'] = NetmikoPromptsService
