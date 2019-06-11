# This class serves as a template example for the user to understand
# how to implement their own custom services to eNMS.
# It can be removed if you are deploying eNMS in production.

# Each new service must inherit from the "Service" class.
# eNMS will automatically generate a form in the web GUI by looking at the
# SQL parameters of the class.
# By default, a property (String, Float, Integer) will be displayed in the GUI
# with a text area for the input.
# If the property in a Boolean, it will be displayed as a tick box instead.
# If the class contains a "property_name_values" property with a list of
# values, it will be displayed:
# - as a multiple selection list if the property is an SQL "MutableList".
# - as a single selection drop-down list in all other cases.
# If you want to see a few examples of services, you can have a look at the
# /netmiko, /napalm and /miscellaneous subfolders in /eNMS/eNMS/services.

# Importing SQL Alchemy column types to handle all of the types of
# form additions that the user could have.
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict, MutableList
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectMultipleField,
    SelectField,
    StringField,
)
from wtforms.validators import (
    Email,
    InputRequired,
    IPAddress,
    Length,
    MacAddress,
    NumberRange,
    Regexp,
    URL,
)

from eNMS.database import SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField
from eNMS.models.automation import Service


class ExampleService(Service):

    __tablename__ = "ExampleService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    # the "string1" property will be displayed as a drop-down list, because
    # there is an associated "string1_values" property in the class.
    string1 = Column(String(SMALL_STRING_LENGTH), default="")
    # the "string2" property will be displayed as a text area.
    string2 = Column(String(SMALL_STRING_LENGTH), default="")
    # string3 is mandatory: in the custom form, the DataRequired validator is used.
    mail_address = Column(String(SMALL_STRING_LENGTH), default="")
    # IP and MAC address
    ip_address = Column(String(SMALL_STRING_LENGTH), default="")
    mac_address = Column(String(SMALL_STRING_LENGTH), default="")
    # Integer field
    an_integer = Column(Integer, default=0)
    # Number range
    number_in_range = Column(Integer, default=5)
    # regex
    regex = Column(String(SMALL_STRING_LENGTH), default="")
    # URL
    url = Column(String(SMALL_STRING_LENGTH), default="")
    # Text area
    a_float = Column(Float, default=0.0)
    # the "a_list" property will be displayed as a multiple selection list
    # list, with the values contained in "a_list_values".
    a_list = Column(MutableList.as_mutable(PickleType))
    # Text area where a python dictionary is expected
    a_dict = Column(MutableDict.as_mutable(PickleType))
    # "boolean1" and "boolean2" will be displayed as tick boxes in the GUI.
    boolean1 = Column(Boolean, default=False)
    boolean2 = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "ExampleService"}

    # Some services will take action or interrogate a device. The job method
    # can also take device as a parameter for these types of services.
    # def job(self, device, payload):
    def job(self, payload: dict) -> dict:
        self.logs.append(f"Real-time logs displayed when the service is running.")
        # The "job" function is called when the service is executed.
        # The parameters of the service can be accessed with self (self.string1,
        # self.boolean1, etc)
        # You can look at how default services (netmiko, napalm, etc.) are
        # implemented in the /services subfolders (/netmiko, /napalm, etc).
        # "results" is a dictionary that will be displayed in the logs.
        # It must contain at least a key "success" that indicates whether
        # the execution of the service was a success or a failure.
        # In a workflow, the "success" value will determine whether to move
        # forward with a "Success" edge or a "Failure" edge.
        return {"success": True, "result": "example"}


class ExampleForm(ServiceForm):
    form_type = HiddenField(default="ExampleService")
    string1 = SelectField(
        choices=[("cisco", "Cisco"), ("juniper", "Juniper"), ("arista", "Arista")]
    )
    string2 = StringField("String 2 (required)", [InputRequired()])
    mail_address = StringField("Mail address", [Length(min=7, max=25), Email()])
    ip_address = StringField(
        "IP address",
        [
            IPAddress(
                ipv4=True,
                message="Please enter an IPv4 address for the IP address field",
            )
        ],
    )
    mac_address = StringField("MAC address", [MacAddress()])
    number_in_range = IntegerField("Number in range", [NumberRange(min=3, max=8)])
    regex = StringField("Regular expression", [Regexp(r".*")])
    url = StringField(
        "URL",
        [
            URL(
                require_tld=True,
                message="An URL with TLD is required for the url field",
            )
        ],
    )
    an_integer = IntegerField()
    a_float = FloatField()
    a_list = SelectMultipleField(
        choices=[("value1", "Value 1"), ("value2", "Value 2"), ("value3", "Value 3")]
    )
    a_dict = DictField()
    boolean1 = BooleanField()
    boolean2 = BooleanField("Boolean N°1")
