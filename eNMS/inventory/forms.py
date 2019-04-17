from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
)

from eNMS.automation.functions import NAPALM_DRIVERS, NETMIKO_DRIVERS
from eNMS.models.base_models import MultipleObjectField, ObjectField
from eNMS.properties import (
    custom_properties,
    pool_link_properties,
    link_subtypes,
    pool_device_properties,
    device_subtypes,
)
