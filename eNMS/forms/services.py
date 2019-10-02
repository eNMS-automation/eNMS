from wtforms import BooleanField, FloatField, HiddenField, IntegerField, SelectField

from eNMS import app
from eNMS.forms import BaseForm
from eNMS.forms.fields import DictField, PasswordSubstitutionField, SubstitutionField


class NetmikoForm(BaseForm):
    form_type = HiddenField(default="netmiko")
    abstract_service = True
    driver = SelectField(choices=app.NETMIKO_DRIVERS)
    use_device_driver = BooleanField(default=True)
    privileged_mode = BooleanField("Privileged mode (run in enable mode or as root)", default=True)
    fast_cli = BooleanField()
    timeout = IntegerField(default=10)
    delay_factor = FloatField(default=1.0)
    global_delay_factor = FloatField(default=1.0)
    group = {
        "commands": [
            "driver",
            "use_device_driver",
            "privileged_mode",
            "fast_cli",
            "timeout",
            "delay_factor",
            "global_delay_factor",
        ],
        "default": "expanded",
    }


class NapalmForm(BaseForm):
    form_type = HiddenField(default="napalm")
    abstract_service = True
    driver = SelectField(choices=app.NAPALM_DRIVERS)
    use_device_driver = BooleanField(default=True)
    timeout = IntegerField(default=10)
    optional_args = DictField()
    group = {
        "commands": ["driver", "use_device_driver", "timeout", "optional_args"],
        "default": "expanded",
    }


class ConnectionForm(BaseForm):
    form_type = HiddenField(default="connection")
    abstract_service = True
    credentials = SelectField(
        "Credentials",
        choices=(
            ("device", "Device Credentials"),
            ("user", "User Credentials"),
            ("custom", "Custom Credentials"),
        ),
    )
    custom_username = SubstitutionField("Custom Username")
    custom_password = PasswordSubstitutionField("Custom Password")
    start_new_connection = BooleanField("Start New Connection")
    close_connection = BooleanField("Close Connection")
    group = {
        "commands": [
            "credentials",
            "custom_username",
            "custom_password",
            "start_new_connection",
            "close_connection",
        ],
        "default": "expanded",
    }
