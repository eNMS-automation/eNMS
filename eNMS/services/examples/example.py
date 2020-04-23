# This class serves as a template example for the user to understand
# how to implement their own custom services to eNMS.

# To create a new service in eNMS, you need to implement:
# - A service class, which defines the service parameters stored in the database.
# - A service form, which defines what is displayd in the GUI.

# SQL Alchemy db.Column types
from sqlalchemy import Boolean, Float, ForeignKey, Integer

# WTForms Field Validators
from wtforms.validators import (
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

from eNMS.database import db
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import (
    BooleanField,
    DictField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectMultipleField,
    SelectField,
    StringField,
)
from eNMS.models.automation import Service


class ExampleService(Service):

    __tablename__ = "example_service"
    pretty_name = "Example"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    # The following fields will be stored in the database as:
    # - String
    string1 = db.Column(db.SmallString)
    string2 = db.Column(db.SmallString)
    mail_address = db.Column(db.SmallString)
    ip_address = db.Column(db.SmallString)
    mac_address = db.Column(db.SmallString)
    regex = db.Column(db.SmallString)
    url = db.Column(db.SmallString)
    exclusion_field = db.Column(db.SmallString)
    # - Integer
    an_integer = db.Column(Integer, default=0)
    number_in_range = db.Column(Integer, default=5)
    custom_integer = db.Column(Integer, default=0)
    # - Float
    a_float = db.Column(Float)
    # - List
    a_list = db.Column(db.List)
    # - Dictionary
    a_dict = db.Column(db.Dict)
    # - Boolean
    boolean1 = db.Column(Boolean, default=False)
    boolean2 = db.Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "example_service"}

    # Some services will take action or interrogate a device. The job method
    # can also take device as a parameter for these types of services.
    # def job(self, device, payload):
    def job(self, run, payload, device=None):
        run.log("info", "Logs displayed in real-time as service runs", device)
        # The "job" function is called when the service is executed.
        # If the service is running on devices, you must add a "device" argument.
        # If it isn't, this "device" argument should be omitted.
        # If the service can run both with and without a device, this key must
        # be made an keyword argument set to None, like here.
        # The parameters of the service can be accessed with self (self.string1,
        # self.boolean1, etc)
        # You can look at how default services (netmiko, napalm, etc.) are
        # implemented in other folders.
        # The resulting dictionary will be displayed in the logs.
        # It can contain a key "success" that indicates whether
        # the execution of the service was a success or a failure.
        # That "success" value will determine whether to move forward with
        # a "Success" edge or a "Failure" edge.
        return {"success": True, "result": "example"}


class ExampleForm(ServiceForm):
    # Each service model must have an corresponding form.
    # The purpose of a form is twofold:
    # - Define how the service is displayed in the UI
    # - Check for each field that the user input is valid.
    # A service cannot be created/updated until all fields are validated.

    # The following line is mandatory: the default value must point
    # to the service.
    form_type = HiddenField(default="example_service")

    # string1 is defined as a "SelectField": it will be displayed as a
    # drop-down list in the UI.
    string1 = SelectField(
        choices=[("cisco", "Cisco"), ("juniper", "Juniper"), ("arista", "Arista")]
    )

    # String2 is a StringField, which is displayed as a standard textbox.
    # The "InputRequired" validator is used: this field is mandatory.
    string2 = StringField("String 2 (required)", [InputRequired()])

    # The main address length must be comprised between 7 and 25 characters
    mail_address = StringField("Mail address", [Length(min=7, max=25)])

    # This IP address validator will ensure the user input is a valid IPv4 address.
    # If it isn't, you can set the error message to be displayed in the GUI.
    ip_address = StringField(
        "IP address",
        [
            IPAddress(
                ipv4=True,
                message="Please enter an IPv4 address for the IP address field",
            )
        ],
    )

    # MAC address validator
    mac_address = StringField("MAC address", [MacAddress()])

    # The NumberRange validator will ensure the user input is an integer
    # between 3 and 8.
    number_in_range = IntegerField("Number in range", [NumberRange(min=3, max=8)])

    # The Regexp field will ensure the user input matches the regular expression.
    regex = StringField("Regular expression", [Regexp(r".*")])

    # URL validation, with or without TLD.
    url = StringField(
        "URL",
        [
            URL(
                require_tld=True,
                message="An URL with TLD is required for the url field",
            )
        ],
    )

    # The NoneOf validator lets you define forbidden value for a field.
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

    # If validator the user input is more complex, you can create a python function
    # to implement the validation mechanism.
    # Here, the custom_integer field will be validated by the "validate_custom_integer"
    # function below.
    # That function will check that the custom integer value is superior to the product
    # of "an_integer" and "a_float".
    # You must raise a "ValidationError" when the validation fails.
    custom_integer = IntegerField("Custom Integer")

    # A SelectMultipleField will be displayed as a drop-down list that allows
    # multiple selection.
    a_list = SelectMultipleField(
        choices=[("value1", "Value 1"), ("value2", "Value 2"), ("value3", "Value 3")]
    )
    a_dict = DictField()

    # A BooleanField is displayed as a check box.
    boolean1 = BooleanField()
    boolean2 = BooleanField("Boolean N°1")

    def validate_custom_integer(self, field):
        product = self.an_integer.data * self.a_float.data
        if field.data > product:
            raise ValidationError(
                "Custom integer must be less than the "
                "product of 'An integer' and 'A float'"
            )
