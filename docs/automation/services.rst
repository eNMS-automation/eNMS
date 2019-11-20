========
Services
========

A service is a Python script that performs an action. A service is defined by:

- A database model. You can define all the parameters you need as SQL Alchemy columns: this is what eNMS stores in the database.
- A form. It defines what is displayed in the UI, and it validates the user inputs.

When the application starts, it loads all python files in ``eNMS/eNMS/services``, and adds all models to the database. Inside the ``eNMS/eNMS/services`` folder, you are free to create subfolders to organize your own services any way you want: eNMS will automatically detect all python files. After adding a new custom service, you must reload the application before it appears in the web UI.
You can create instances of a service from the web UI.
eNMS looks at the form class to auto-generate a form for the user to create new instances of that service.

eNMS comes with a list of "default" services based on network automation frameworks such as ``netmiko``, ``napalm`` and ``ansible``.

Custom Services Path
--------------------

By default, eNMS will scan the ``eNMS/eNMS/services`` folder to instantiate all services you created in that folder.
If you want eNMS to scan another folder (e.g to not have custom services in eNMS .git directory, so that you can safely pull the latest code from Github), you can set the ``custom_services`` variable in the configuration.

Service Management
------------------

Once a service has been customized with parameters, devices selected, etc, we refer to it as a Service Instance. All Service Instances are displayed in the :guilabel:`automation/service_management` page in the ``Automation`` section.

.. image:: /_static/automation/services/service_management.png
   :alt: Service Management page
   :align: center

From the :guilabel:`automation/service_management` page, you can:

- Start a Service Instance (``Run`` button).
- View and compare the results of the Service Instance.
- Edit or duplicate the Service Instance.
- Export the Service Instance: the service instance will be exported as a YaML file in the ``files/exported_services`` directory. This allows migrating service instances from one VM to another if you are using different VM.
- Delete the Service Instance.

When running a service instance, the device progress (current device/total devices selected to run) will be displayed in the table, unless Multiprocessing is selected to run the devices in parallel, in which case eNMS cannot keep track of how many devices are completed until the service instance finishes.
Each field in the table allows for searching that field by inclusion match.

Service device targets
----------------------

When you create a new Service Instance, the form will also contain multiple selection fields for you to select "devices".

.. image:: /_static/automation/services/device_selection.png
   :alt: Device selection
   :align: center

There are two ways to select devices:

- Directly from the "Devices" and "Pools" drop-down. The service will run on all selected devices, as well as on the devices of all selected pools.
- With a python query to extract devices (either IP address or names) from the payload.
The python query can use the variables and functions described in the "Advanced" section of the documentation.

A service can run on its devices either sequentially, or in parallel if the ``Multiprocessing`` checkbox is ticked.
Some services have no devices at all: it depends on what the service is doing.

Variable substitution
---------------------

For some services, it is useful for a string to include variables such as a timestamp or device parameters.
For example, if you run a ReST call script on several devices to send a request at a given URL, you might want the URL to depend on the name of the device.
Any code between double curved brackets will be evaluated at runtime and replaced with the appropriate value.

For example, you can POST a request on several devices at ``/url/{{device.name}}``, and ``{{device.name}}`` will be replaced on each execution iteration by the name of each device.

Let's consider the following ReST call service:

.. image:: /_static/automation/services/variable_substitution.png
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

In addition to the services provided by default, you are free to create your own "custom" services.
Creating a custom services means adding a new python file in the ``eNMS/eNMS/services`` folder.
This python file must contain:

- A model class, where you define what the service parameters are, and what the service is doing (``job`` function).
- A form class, where you define what the service looks like in the GUI: the different fields in the service form and their corresponding validation.

Custom services
---------------

Create a new service model
**************************

In ``eNMS/eNMS/services/examples``, you will find the file ``example_service.py`` with a service template
that you can use as starting point to create your own services. 

Swiss Army Knife Service
************************

Whenever your services require input parameters, eNMS automatically displays a form in the UI.
The "Swiss Army Knife Service" acts as a catch-all of utility methods that do not require GUI input.  It also serves to reduce the number of custom Services that a user might need, and thus reduces the complexity of performing database migrations across those Services.

Another use-case is to implement a service that will only exist as a single instance, and therefore does not need any variable parameter.
This can be done with the ``Swiss Army Knife Service``.

A "Swiss Army Knife Service" has only one parameter: a name. The function that will run when this service is scheduled is the one that carries the same name as the service itself.
The "Swiss Army Knife Service" ``job`` function can be seen as a "service multiplexer".

Let's take a look at how the ``Swiss Army Knife Service`` is implemented:

::

 class SwissArmyKnifeService(Service):

     __tablename__ = "swiss_army_knife_service"

     id = Column(Integer, ForeignKey("service.id"), primary_key=True)
     has_targets = Column(Boolean, default=False)

     __mapper_args__ = {"polymorphic_identity": "swiss_army_knife_service"}

     def job(self, *args):
         return getattr(self, self.name)(*args)

    def job1(self, payload):
        return {'success': True, 'result': ''}

    def job2(self, payload):
        return {'success': True, 'result': ''}

The ``job`` function of ``SwissArmyKnifeService`` will run the class method of ``SwissArmyKnifeService`` with the same name as the instance itself.

In other words, with the above code, you can create two instances of SwissArmyKnifeService from the web UI: one named "job1" and the other named "job2". The SwissArmyKnifeService class will take care of calling the right "job" function based on the name of the instance.

The SwissArmyKnifeService also has a parameter ``has_targets`` that defines whether or not the service will use the devices selected upon creating a new instance. If ``has_targets`` is selected, the SwissArmyKnifeService ``job`` function will take an additional device argument, and it will run the instance-name-specified job function on each selected device.  You can use the device properties (IP address, operating system, etc) however you need within the job function(s).

Helper function
***************

In your custom python code, there is a number of function that are made available by eNMS and that you can reuse:

- Netmiko connection (``netmiko_connection = run.netmiko_connection(device)``)
give you a working netmiko connection, and takes care of caching the connection when running inside a workflow.
- Napalm connection (``napalm_connection = run.napalm_connection(device)``)
give you a working napalm connection, and takes care of caching the connection when running inside a workflow.
- Send email (``controller.send_email``) lets you send an email with optional attached file.

::

  controller.send_email(
      title,
      content,
      sender=sender,
      recipients=recipients,
      filename=filename,
      file_content=file_content
  )
