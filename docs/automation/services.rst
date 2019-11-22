========
Services
========

A service is a Python script that performs an action. A service is defined by:

- A model: what eNMS stores in the database.
- A form: what eNMS displays in the UI.

eNMS comes with a number of "default" services based on network automation frameworks such as
``netmiko``, ``napalm`` and ``ansible``, but you are free to create your own services.

Service Management
------------------

All services are displayed in the :guilabel:`Automation / Services` page in the ``Automation`` section,
where you can edit, duplicate, delete, export and run existing services, and create new ones.
Export creates a YaML representation of a service in the ``files / exported_services`` directory.
This allows migrating services from one VM to another if you are using multiple VMs.

.. image:: /_static/automation/services/service_management.png
   :alt: Service Management page
   :align: center

Service panel
-------------

General
*******

- ``Name`` Service Instance names (must be unique).
- ``Description`` Freeform description of what the service instance does
- ``Vendor`` Label the service instance with a vendor identifier string. This is useful in sorting and searching service instances.
- ``Operating System`` Label the service instance with an operating system identifier string. This is useful in sorting and searching service instances.
- ``Number of retries`` Add a number of retry attempts for targets that have reliability issues and occassionally fail. See the previous section on Retry Mechanism for more details.
- ``Time between retries (in seconds)`` Specify a number of seconds to wait before attempting the service instance again when a failure occurs.

Specific
********

Workflow
********

- ``Waiting time (in seconds)`` How many seconds to wait after the service instance has completed running before running the next service.

Devices
*******

Some services have no devices at all: it depends on what the service is doing.

There are two ways to select devices:

- Directly from the "Devices" and "Pools" drop-down. The service will run on all selected devices,
as well as on the devices of all selected pools.
- With a python query to extract devices (either IP address or names) from the payload.
The python query can use the variables and functions described in the "Advanced" section of the documentation.

- ``Devices`` Multi-selection list of devices from the inventory
- ``Pools`` (Filtered) pools of devices can be selected instead of, or in addition to, selecting individual devices. Multiple pools may also be selected.
- ``Multiprocessing`` A service can run on its devices either sequentially, or in parallel if the ``Multiprocessing`` checkbox is ticked.
Checkbox enables parallel execution behavior when multiple devices are selected. See the document section on the Workflow System and Workflow Devices for discussion on this behavior.
- ``Maximum Number of Processes`` Set the maximum number of device processes allowed per service instance (assumes devices selected at the service instance level)
- ``Credentials`` Choose between device credentials from the inventory or user credentials (login credentials for the eNMS user) when connecting to each device.

Iteration
*********

Validation
**********

Notification
************

- ``Send Notification`` Enable sending results notification checkbox
- ``Send Notification Method`` Choose Mail, Mattermost, or Slack to send the results summary to. See the previous section on Service Notification for more details.
- ``Display only failed nodes`` Include only the failed devices in the email notification body summary
- ``Mail Recipients (separated by comma)`` Overrides the Mail Recipients specified in the Administration Panel

Variable substitution
---------------------

For some services, it is useful for a string to include variables such as a timestamp or device parameters.
For example, if you run a REST call script on several devices to send a request at a given URL, you might want the URL to depend on the name of the device.
Any code between double curved brackets will be evaluated at runtime and replaced with the appropriate value.

For example, you can POST a request on several devices at ``/url/{{device.name}}``, and ``{{device.name}}`` will be replaced on each execution iteration by the name of each device.

Let's consider the following REST call service:

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

When the application starts, it loads all python files in , and adds all models to the database.
Inside the ``eNMS/eNMS/services`` folder, you are free to create subfolders to organize your own services
any way you want: eNMS will automatically detect all python files.
After adding a new custom service, you must reload the application before it appears in the web UI.
In ``eNMS/eNMS/services/examples``, you will find the file ``example_service.py`` with a service template
that you can use as starting point to create your own services.
By default, eNMS will scan the ``eNMS/eNMS/services`` folder to instantiate all services you created in that folder.
If you want eNMS to scan another folder (e.g to not have custom services in eNMS .git directory,
so that you can safely pull the latest code from Github), you can set the ``custom_services``
variable in the configuration.

Swiss Army Knife Service
************************

Whenever your services require input parameters, eNMS automatically displays a form in the UI.
The "Swiss Army Knife Service" acts as a catch-all of utility methods that do not require GUI input,
and will only exist as a single instance.
It also serves to reduce the number of custom services that a user might need, and thus reduces the complexity
of performing database migrations.

A "Swiss Army Knife Service" has only one parameter: a name. The function that will run when this
service is scheduled is the one that carries the same name as the service itself.
The "Swiss Army Knife Service" ``job`` function can be seen as a "service multiplexer".

Available functions
*******************

In your custom python code, there is a number of function that are made available by eNMS and that you can reuse:

- Netmiko connection (``netmiko_connection = run.netmiko_connection(device)``)
give you a working netmiko connection, and takes care of caching the connection when running inside a workflow.
- Napalm connection (``napalm_connection = run.napalm_connection(device)``) does the same thing for Napalm.
- Send email (``app.send_email``) lets you send an email with optional attached file.

::

  app.send_email(
      title,
      content,
      sender=sender,
      recipients=recipients,
      filename=filename,
      file_content=file_content
  )
