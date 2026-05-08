from re import sub
from ruamel.yaml import YAML
from uuid import uuid4
from eNMS.variables import vs


class CustomApp(vs.TimingMixin):
    def generate_uuid(self):
        return str(uuid4())

    def log_post_processing(_self, **kwargs):
        return

    def parse_configuration_property(self, device, property, value=None):
        if not value:
            value = getattr(device, property)
        if device.operating_system == "EOS" and property == "configuration":
            value = sub(r"(username.*secret) (.*)", "\g<1> ********", value)
        return value

    def run_post_processing(self, run, run_result):
        return

    def runner_global_variables(self, run):
        return {}

    def server_template_context(self):
        return {}

vs.custom = CustomApp()
