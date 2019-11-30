========
Services
========

A service is a Python script that performs an action. A service is defined by:

- A model: what eNMS stores in the database.
- A form: what eNMS displays in the UI.

eNMS comes with a number of "default" services based on network automation frameworks such as
``netmiko``, ``napalm`` and ``ansible``, but you are free to create your own services.
Each service will return a python dictionary as a result. This dictionary will always contains
a ``success`` boolean value that indicates whether it ran successfully or not.

Service Management
------------------

All services are displayed in :guilabel:`Automation / Services` , where you can edit, duplicate,
delete, export and run existing services, and create new ones.
Export creates a YaML representation of a service in the ``files / exported_services`` directory.
This allows migrating services from one VM to another if you are using multiple VMs.

.. image:: /_static/automation/services/services.png
   :alt: Service Management page
   :align: center

Service panel
-------------

General
*******

- ``Name`` (**mandatory**) Must be unique.
- ``Description`` / ``Vendor`` / ``Operating System`` Useful for filtering services in the table.
- ``Number of retries`` (default: ``0``) Number of retry attempts when the service fails (per-device if the
  service has device targets).
- ``Time between retries (in seconds)`` (default: ``10``) Number of seconds between each attempt.

.. note:: The retry will affect only the devices for which the service failed. Let's consider a service configured
to run on 3 devices D1, D2, and D3 with 2 "retries". If it fails on D2 and D3 when the service runs for the first time,
eNMS will run the service again for D2 and D3 at the first retry. If D2 succeeds and D3 fails, the second and last
retry will run on D3 only.

Specific
********

This section contains all parameters that are specific to the service type. For the "Netmiko Configuration"
service that uses Netmiko to push a configuration, you will find Netmiko parameters (delay factor,
timeout, etc) and a field to enter the configuration that you want to push.
The content of this section is described for each service in the ``Default Services`` section of the docs.

Workflow
********

This section contains the parameters that apply **when the service runs inside a workflow only**.

- ``Skip this Service Regardless`` Always skip the service
- ``Skip Service If Python Query evaluates to True`` This fields expect a python code that will evaluates to either ``True``
  or ``False``. The service will be skipped or not depending the result.
- ``Maximum number of runs`` (default: ``1``) Number of time a service is allowed to run in a workflow (de
- ``Waiting time (in seconds)`` (default: ``0``) Number of seconds to wait after the service is done running.

Devices
*******

Most services are designed to run on devices from the inventory. There are three properties for selecting devices.
The list of targets will be the union of all devices coming from these properties.

- ``Devices`` Direct selection by device names
- ``Pools`` Direct selection from pools. The set of all devices from all selected pools will be used.
- ``Device query`` and ``Query Property Type`` Programmatic selection with a python query

  - ``Device query`` Query that must return an **iterable** (e.g python list) of **strings (either IP addresses or names)**.
  - ``Query Property Type`` Indicates whether the iterable contains IP addresses of names, for eNMS to convert the list
    to actual devices from the inventory.

- ``Multiprocessing`` Run on devices **in parallel** instead of **sequentially**.
- ``Maximum Number of Processes`` (default: ``5``)

Iteration
*********

Validation
**********

- ``Conversion Method`` (default: ``No conversion``) Some services will fetch a result from an external source.
  There are three conversion modes:

  - ``Text`` Convert the result to a python string.
  - ``JSON`` Convert a string representing JSON data to a python dictionary.
  - ``XML`` Convert a string representing XML data to a python dictionary.

- ``Validation Method`` The validation method depends on whether the result is a string or a dictionary.

  - ``Text match`` Matches the result against ``Content Match`` (string inclusion, or regular expression if 
    ``Match content against Regular expression`` is selected)
  - ``dictionary Equality`` Check for equality against the dictionary provided in ``Dictionary Match``
  - ``dictionary Inclusion`` Check for dictionary inclusion, in the sense that all ``key`` : ``value`` pairs from
    the dictionary provided in ``Dictionary Match`` can be found in the result.

- ``Negative Logic`` Reverses the ``success`` boolean value in the results.
- ``Delete spaces before matching`` (``Text`` match only) Removes white spaces and carraige returns
  in the result and ``Content Match`` (spaces and newlines can cause the match to fail)

Notification
************

When a service finishes, you can choose to receive a notification with the results. There are three types of notification:

- Mail notification: eNMS sends a mail to the address(es) of your choice.
- Slack notification: eNMS sends a message to a channel of your choice.
- Mattermost notification: same as Slack, with Mattermost.

You can configure the following parameters:

- ``Send notification`` Enable sending results notification
- ``Notification Method`` Mail, Slack or Mattermost.
- ``Notification header`` A header displayed at the beginning of the notification.
- ``Include Result Link in summary``: whether the notification contains a link to the results.
- ``Mail recipients`` Must be a list of email addresses, separated by comma. if left empty, the recipients defined
  in the configuration.
- ``Display only failed nodes`` the notification will not include devices for which the service ran successfully.

To set up the mail system, you must set the variable of the ``mail`` section in the configuration.
``server``, ``port``, ``use_tls``, ``username``, ``sender``, ``recipients``.
Besides, you must set the password via the ``MAIL_PASSWORD`` environment variable.

The ``Mail Recipients`` parameter must be set for the mail system to work; the `Admin / Administration` panel parameter can
also be overriden from Step2 of the Service Instance and Workflow configuration panels. For Mail notification, there is
also an option in the Service Instance configuration to display only failed objects in the email summary versus seeing a
list of all passed and failed objects.

In Mattermost, if the ``Mattermost Channel`` is not set, the default ``Town Square`` will be used.

Using python code in the service panel
--------------------------------------

There are many places in the service panel where the user is allowed to use pure python code.
Depending on the context, a number of global variables is made available by eNMS.

Global variables
****************

- ``device`` (Available when the service is running on a device) Current device.
- ``config`` (Always available) Configuration. This is a python dictionary available in
  :guilabel:`Admin / Administration`, button ``Configuration``. By default, it is set to the content
  of ``config.json``.
- ``workflow`` (Available when the service runs inside a workflow) Current workflow.
- ``parent_device`` (Available when the iteration mechanism is used) Parent device, from which the actual
  targets of the service are computed.

Variable Substitution
*********************

There are some fields 
For some services, it is useful for a string to include variables such as a timestamp or device parameters.
For example, if you run a REST call script on several devices to send a request at a given URL, you might
want the URL to depend on the name of the device.
Any code between double curved brackets will be evaluated at runtime and replaced with the appropriate value.

For example, you can POST a request on several devices at ``/url/{{device.name}}``, and ``{{device.name}}``
will be replaced on each execution iteration by the name of each device.

Let's consider the following REST call service:

.. image:: /_static/automation/services/variable_substitution.png
   :alt: Variable substitution
   :align: center

When this service is executed, the following GET requests will be sent in parallel:

```
INFO:werkzeug:127.0.0.1 - - [13/Oct/2018 14:07:49] "GET /rest/object/device/router18 HTTP/1.1" 200 -
INFO:werkzeug:127.0.0.1 - - [13/Oct/2018 14:07:49] "GET /rest/object/device/router14 HTTP/1.1" 200 -
INFO:werkzeug:127.0.0.1 - - [13/Oct/2018 14:07:49] "GET /rest/object/device/router8 HTTP/1.1" 200 -
```



- Inside double curved brackets in the service parameters (``{{python expression}}``). This is called "Variable substitution" (fields that support variable substitution are marked with a light blue background).
- In the ``Device Query`` field of the "Devices" section of a service. This field lets the user define the targets of a service programmatically.
- In the ``Skip Service If Python Query evaluates to True`` field of the "Workflow" section of a service. This field lets the user define whether or not a service should be skipped programmatically.
- In the ``Query`` field of the Variable Extraction Service.
- In the code of a Python Snippet Service.

And the following functions:

- ``get_var`` and ``set_var``: function to save data to and retrieve data from the payload.
    The use of these two functions is explained in the section ""Set and get data in a workflow" of the workflow payload docs.
- ``get_result``: function to retrieve a result for a given service (and for an optional device).
    The use of this function is described in the section "Use data from a previous service in the workflow" of the workflow payload docs.



Validation
----------

For some services, the success or failure of the service is decided by a "Validation" process.
The validation can consist in:

- Looking for a string in the output of the service.
- Matching the output of the service against a regular expression.
- Anything else: you can implement any validation mechanism you want in your custom services.

In addition to text matching, for some services where output is either expected in JSON/dictionary format, or where expected XML output can be converted to dictionary format, matching against a dictionary becomes possible:

- Dictionary matching can be by inclusion:  Are all "key:value" pairs included in the output?
- Dictionary matching can be by equality: Are all provided "key:value" pairs exactly matching the output key:value pairs?

A few options are available to the user:

- ``Negative logic``: the result is inverted: a success becomes a failure and vice-versa. This prevents the user from using negative look-ahead regular expressions.
- ``Delete spaces before matching``: the output returned by the device will be stripped from all spaces and newlines, as those can sometimes result in false negative.

Custom services
---------------

In addition to the services provided by default, you are free to create your own "custom" services.
Creating a custom services means adding a new python file in the ``eNMS/eNMS/services`` folder.
This python file must contain:

- A model class, where you define what the service parameters are, and what the service is doing (``job`` function).
- A form class, where you define what the service looks like in the GUI: the different fields in the service form and
their corresponding validation.

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
