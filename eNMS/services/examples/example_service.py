# This class serves as a template example for the user to understand
# how to implement their own custom services to eNMS.

# To create a new service in eNMS, you need to implement:
# - A service class, which defines the service parameters stored in the database.
# - A service form, which defines what is displayd in the GUI.

# SQL Alchemy Column types
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict, MutableList
# WTForms Fields
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectMultipleField,
    SelectField,
    StringField,
)
# WTForms Field Validators
from wtforms.validators import (
    Email,
    InputRequired,
    IPAddress,
    Length,
    MacAddress,
    NoneOf,
    NumberRange,
    Regexp,
    URL,
    ValidationError,
)

from eNMS.database import SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField
from eNMS.models.automation import Service


class ExampleService(Service):

    __tablename__ = "ExampleService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    # The following fields will be stored in the database as:
    # - String
    string1 = Column(String(SMALL_STRING_LENGTH), default="")
    string2 = Column(String(SMALL_STRING_LENGTH), default="")
    mail_address = Column(String(SMALL_STRING_LENGTH), default="")
    ip_address = Column(String(SMALL_STRING_LENGTH), default="")
    mac_address = Column(String(SMALL_STRING_LENGTH), default="")
    regex = Column(String(SMALL_STRING_LENGTH), default="")
    url = Column(String(SMALL_STRING_LENGTH), default="")
    exclusion_field = Column(String(SMALL_STRING_LENGTH), default="")
    # - Integer
    an_integer = Column(Integer, default=0)
    number_in_range = Column(Integer, default=5)
    custom_integer = Column(Integer, default=0)
    # - Float
    a_float = Column(Float, default=0.0)
    # - List
    a_list = Column(MutableList.as_mutable(PickleType))
    # - Dictionary
    a_dict = Column(MutableDict.as_mutable(PickleType))
    # - Boolean
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
        # implemented in other folders.
        # The resulting dictionary will be displayed in the logs.
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
    exclusion_field = StringField(
        "Exclusion field",
        [
            NoneOf(
                ("a", "b", "c"),
                message=(
                    "'a', 'b', and 'c' are not valid " "inputs for the exclusion field"
                ),
            )
        ],
    )
    an_integer = IntegerField()
    a_float = FloatField()
    custom_integer = IntegerField("Custom Integer")
    a_list = SelectMultipleField(
        choices=[("value1", "Value 1"), ("value2", "Value 2"), ("value3", "Value 3")]
    )
    a_dict = DictField()
    boolean1 = BooleanField()
    boolean2 = BooleanField("Boolean N°1")

    def validate_custom_integer(self, field: IntegerField) -> None:
        product = self.an_integer.data * self.a_float.data
        if field.data > product:
            raise ValidationError(
                "Custom integer must be less than the "
                "product of 'An integer' and 'A float'"
            )
