========
Services
========

A service is a Python script that performs an action. A service is defined by:

- A database model. You can define all the parameters you need as SQL Alchemy columns: this is what eNMS stores in the database.
- A form. It defines what is displayed in the UI, and it validates the user inputs.

In ``eNMS/eNMS/services/examples``, you will find the file ``example_service.py`` with a service template that you can use as starting point to create your own services. 
This file contains the following code :

::

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
      def job(self, run: "Run", payload: dict) -> dict:
          run.log("info", f"Real-time logs displayed when the service is running.")
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
      # Each service model must have an corresponding form.
      # The purpose of a form is twofold:
      # - Define how the service is displayed in the UI
      # - Check for each field that the user input is valid.
      # A service cannot be created/updated until all fields are validated.

      # The following line is mandatory: the default value must point
      # to the service.
      form_type = HiddenField(default="ExampleService")

      # string1 is defined as a "SelectField": it will be displayed as a
      # drop-down list in the UI.
      string1 = SelectField(
          choices=[("cisco", "Cisco"), ("juniper", "Juniper"), ("arista", "Arista")]
      )

      # String2 is a StringField, which is displayed as a standard textbox.
      # The "InputRequired" validator is used: this field is mandatory.
      string2 = StringField("String 2 (required)", [InputRequired()])

      # The main address field uses two validators:
      # - The input length must be comprised between 7 and 25 characters
      # - The input syntax must match that of an email address.
      mail_address = StringField("Mail address", [Length(min=7, max=25), Email()])

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

      def validate_custom_integer(self, field: IntegerField) -> None:
          product = self.an_integer.data * self.a_float.data
          if field.data > product:
              raise ValidationError(
                  "Custom integer must be less than the "
                  "product of 'An integer' and 'A float'"
              )


When the application starts, it loads all python files in ``eNMS/eNMS/services``, and adds all models to the database. Inside the ``eNMS/eNMS/services`` folder, you are free to create subfolders to organize your own services any way you want: eNMS will automatically detect all python files. After adding a new custom service, you must reload the application before it appears in the web UI.
You can create instances of a service from the web UI.
eNMS looks at the form class to auto-generate a form for the user to create new instances of that service.

For the ``ExampleService`` service displayed above, the associated auto-generated form is the following (not all fields are displayed):

.. image:: /_static/services/service_system/example_service.png
   :alt: Example service
   :align: center

eNMS comes with a list of "default" services based on network automation frameworks such as ``netmiko``, ``napalm`` and ``ansible``.

Custom Services Path
--------------------

By default, eNMS will scan the ``eNMS/eNMS/services`` folder to instantiate all services you created in that folder.
If you want eNMS to scan another folder (e.g to not have custom services in eNMS .git directory, so that you can safely pull the latest code from Github), you can set the ``CUSTOM_SERVICES_PATH`` environment variable to the path of the folder that contains your custom services.

Service Management
------------------

Once a service has been customized with parameters, devices selected, etc, we refer to it as a Service Instance. All Service Instances are displayed in the :guilabel:`automation/service_management` page in the ``Automation`` section.

.. image:: /_static/services/service_system/service_management.png
   :alt: Service Management page
   :align: center

From the :guilabel:`automation/service_management` page, you can:

- Start a Service Instance (``Run`` button).
- View and compare the results of the Service Instance.
- Edit or duplicate the Service Instance.
- Export the Service Instance: the service instance will be exported as a YaML file in the ``projects/exported_jobs`` directory. This allows migrating service instances from one VM to another if you are using different VM.
- Delete the Service Instance.

When running a service instance, the device progress (current device/total devices selected to run) will be displayed in the table, unless Multiprocessing is selected to run the devices in parallel, in which case eNMS cannot keep track of how many devices are completed until the service instance finishes.
Each field in the table allows for searching that field by inclusion match.

Service device targets
----------------------

When you create a new Service Instance, the form will also contain multiple selection fields for you to select "devices".

.. image:: /_static/services/service_system/device_selection.png
   :alt: Device selection
   :align: center

There are two ways to select devices:

- Directly from the "Devices" and "Pools" drop-down. The service will run on all selected devices, as well as on the devices of all selected pools.
- From the payload when the service runs inside a workflow. You can tick the ``Define devices from payload`` box and write a YaQL query to extract devices (either IP address or names) from the payload.

A service can run on its devices either sequentially, or in parallel if the ``Multiprocessing`` checkbox is ticked.
Some services have no devices at all: it depends on what the service is doing.

Variable substitution
---------------------

For some services, it is useful for a string to include variables such as a timestamp or device parameters.
For example, if you run a ReST call script on several devices to send a request at a given URL, you might want the URL to depend on the name of the device.
Any code between double curved brackets will be evaluated at runtime and replaced with the appropriate value.

For example, you can POST a request on several devices at ``/url/{{device.name}}``, and ``{{device.name}}`` will be replaced on each execution iteration by the name of each device.

Let's consider the following ReST call service:

.. image:: /_static/services/service_system/variable_substitution.png
   :alt: Variable substitution
   :align: center

When this service is executed, the following GET requests will be sent in parallel:

::

  INFO:werkzeug:127.0.0.1 - - [13/Oct/2018 14:07:49] "GET /rest/object/device/router18 HTTP/1.1" 200 -
  INFO:werkzeug:127.0.0.1 - - [13/Oct/2018 14:07:49] "GET /rest/object/device/router14 HTTP/1.1" 200 -
  INFO:werkzeug:127.0.0.1 - - [13/Oct/2018 14:07:49] "GET /rest/object/device/router8 HTTP/1.1" 200 -

Variable substitution is also valid in a configuration string (for a Netmiko or Napalm configuration) service, as well as a validation string (Netmiko validation service, Ansible playbook, etc).

Validation
----------

For some services, the success or failure of the service is decided by a "Validation" process.
The validation can consist in:

- Looking for a string in the output of the service.
- Matching the output of the service against a regular expression.
- Anything else: you can implement any validation mechanism you want in your custom services.

In addition to text matching, for some services where output is either expected in JSON/dictionary format, or where expected XML output can be converted to dictionary format, matching against a dictionary becomes possible:

- Dictionary matching can be by inclusion:  Are my provided key:value pairs included in the output?
- Dictionary matching can be by equality: Are my provided key:value pairs exactly matching the output key:value pairs?

A few options are available to the user:

- ``Negative logic``: the result is inverted: a success becomes a failure and vice-versa. This prevents the user from using negative look-ahead regular expressions.
- ``Delete spaces before matching``: the output returned by the device will be stripped from all spaces and newlines, as those can sometimes result in false negative.

Retry mechanism
---------------

Each service can be configured to run again in case of failures.
There are two parameters to configure:

- The number of retries (default: 0)
- The time between retries (default: 10 seconds)

.. note:: The retry will affect only the devices for which the service failed. Let's consider a service configured to run on 3 devices D1, D2, and D3 with 2 "retries". If it fails on D2 and D3 when the service runs for the first time, eNMS will run the service again for D2 and D3 at the first retry. If D2 succeeds and D3 fails, the second and last retry will run on D3 only.
