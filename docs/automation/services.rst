========
Services
========

Services provide the smallest unit of automation in eNMS.  Each service type provides unique functionality that is
easily configured to perform complex operations in the network.  Examples: remote command execution, ReST API calls,
Ansible playbook execution, and many more.

Services can be powerful on their own, (e.g. ping all devices in the network and send a status email).
They can also be combined within workflows to automate complex operations such as device upgrades.

Each service type provides a form for configuring its unique functionality.  Common forms are available on every service
for defining device targets, iteration, retries, pre and post processing, result validation, notifications, etc.

eNMS comes with a number of "default" services based on network automation frameworks such as
``netmiko``, ``napalm`` and ``ansible``, but you are free to create your own custom service types.
Each service must return a python dictionary as a result.

All services are displayed in :guilabel:`Automation / Services`, where you can create new services and
edit, duplicate, delete, and run existing ones.

.. image:: /_static/automation/services/services.png
   :alt: Service Management page
   :align: center

A service type is a Python script that performs an action. A service type is defined by:

- A **model** class: the service parameters, and what the service is doing via a ``job`` function.
- A **form** class: the different fields eNMS displays in the UI, and their corresponding validation.


.. note::

  You can also export services: this creates a YAML file with all service properties in the
  ``files / exported_services`` directory.
  This allows migrating services from one VM to another if you are using multiple VMs.

Service Panel
-------------

Section ``General``
*******************

Main Parameters
"""""""""""""""

- ``Scoped Name`` (**mandatory**) Must be unique either within the enclosing workflow or unique among top-level services.
- ``Name`` (**display only**) Fully qualified service name including all workflow nesting and a **[Shared]** tag.
- ``Service Type`` (**display only**) The service type of the current service instance.
- ``Shared`` Checked for **Shared** services.  Once set, this value cannot be changed.

.. note:: Services can be standalone, shared, or scoped within a workflow. Shared services (or subworkflows) can exist
  inside multiple workflows, and a change to a shared service affects all workflows that use it. A service which is scoped
  within a workflow, either by creating the service inside the workflow or by deep copying the service into the workflow,
  exists only inside that workflow, so changes to it only affect its parent workflow.  A standalone service exists outside
  of any workflow. A superworkflow acts as a template or wrapper around another workflow and allows for services to be run
  before and after the main workflow (which exists inside the superworkflow as a Placeholder). Because multiple workflows
  can specify the same superworkflow, the superworkflow acts as if it is shared.

- ``Workflows`` (**display only**) Displays the list of workflows that reference the service.
- ``Description`` / ``Vendor`` / ``Operating System`` Useful for filtering services in the table.
- ``Initial Payload`` User-defined dictionary that can be used anywhere in the service.

.. note:: The retry will affect only the devices for which the service failed. Let's consider a service configured to run on 3 devices D1, D2, and D3 with 2 "retries". If it fails on D2 and D3 when the service runs for the first time, eNMS will run the service again for D2 and D3 at the first retry. If D2 succeeds and D3 fails, the second and last retry will run on D3 only.

- ``Number of retries`` (default: ``0``) Number of retry attempts when the service fails (if the service has device targets, this
  is the number of retries for each device).
- ``Time between retries (in seconds)`` (default: ``10``) Number of seconds to wait between each attempt.
- ``Maximum number of retries (loop prevention mechanism)`` (default: ``100``) Used to prevent infinite loops in workflows
  with circular paths.
- ``Logging`` (default: ``Info``) The log level to use when running the service; it governs logs written to the log window
  in the UI, as well as the logs that are written to the log files.

Workflow Parameters
"""""""""""""""""""

This section contains the parameters that apply **when the service runs inside a workflow only**.

- ``Preprocessing`` Section where you can write a python script that will run before the service is executed. If the service has
  device targets, the code will be executed for each device independently, and a ``device`` global variable is available.
  Note: Preprocessing is executed for standalone services and those within a workflow.
- ``Skip`` If ticked, the service is skipped.
- ``Skip Query`` This fields expect a python expression that evaluates to either ``True``
  or ``False``. The service will be skipped if ``True`` and will run otherwise.
- ``Skip Value`` Defines the success value of the service when skipped (in a workflow, the success value will define whether to follow the
  success path (success edge) or the failure path (failure edge).
- ``Maximum number of runs`` (default: ``1``) Number of times a service is allowed to run in a workflow
- ``Time to Wait before next service is started (in seconds)`` (default: ``0``) Number of seconds to wait after the service is done running.

Custom Properties
"""""""""""""""""
The Custom Properties section allows each instance of eNMS to add extra properties to the service form.  Additional
information for these fields may be available using the help icon next to the field label.

The location for the help file can specified in the ``setup/properties.json`` file like this:
  - "render_kw":  { "help": "custom/impacting" }

Section ``Specific``
********************

This section contains all parameters that are specific to the service type. For instance, the "Netmiko Configuration"
service that uses Netmiko to push a configuration will display Netmiko parameters (delay factor,
timeout, etc) and a field to enter the configuration that you want to push.

The content of this section is described for each service in the ``Default Services`` section of the docs.

Section ``Targets``
*******************

Devices
"""""""

Most services are designed to run on devices from the inventory. There are three properties for selecting devices.
The full list of targets is the union of all devices coming from these properties.

- ``Run Method`` Defines whether the service should run once, or if it should run once per device. Most default services are designed
  to run once per device.
- ``Devices`` Direct selection by device names
- ``Pools`` and ``Update pools before running``

  - ``Pools`` Direct selection from pools. The set of all devices from all selected pools is used.
  - ``Update pools before running`` When selected, the pools are updated before reading their set of devices.

- ``Device query`` and ``Query Property Type`` Programmatic selection with a python query

  - ``Device query`` Query that must return an **iterable** (e.g python list) of **strings (either IP addresses or names)**.
  - ``Query Property Type`` Indicates whether the iterable contains IP addresses or names, for eNMS to look up actual devices from the inventory.

- ``Multiprocessing`` Run on devices **in parallel** instead of **sequentially**.
  - Only standalone services and services run in a workflow using a service by service run method benefit from this option.
  - Services in a workflow with run method **Run the workflow device by device** only have a single device.  Instead, use multiprocessing on the workflow.
- ``Maximum Number of Processes`` (default: ``15``) The maximum number of concurrent threads for this service when multiprocessing is enabled.

Iteration
"""""""""

Multiple actions are sometimes necessary when the service is triggered for a target device.  Use iteration devices when
those actions should be performed on a set of devices related to the current target device.  Use iteration values when
the actions should be performed on the current target device.

- ``Iteration Devices`` Query that returns an **iterable** (e.g. Python list) of **strings (either IP addresses or names)**.

  - The service is run for each device as the target device, allowing operations against a set of devices related to the original target.
  - ``Iteration Devices Property`` Indicates whether iterable ``Iteration Devices`` contains IP addresses or names, for eNMS to look up actual devices from the inventory.

- ``Iteration Values`` Query that returns an **iterable** (e.g. Python list) of **strings**.

  - The service is run for each value.
  - ``Iteration Variable Name`` Python variable name to contain each successive value from the ``Iteration Values`` query.


Section ``Result``
*******************

The ``Result`` section defines operations on the service result.  Each form group offers a different type of results
operation.  These operations are performed in the order found on the ``Result`` page.  Result operations are executed
for each device for ``Run method`` **Run the service once for each device**, and are executed only once for
``Run method`` **Run the service once**.


Python Postprocessing
"""""""""""""""""""""

Python can be used to inspect or modify the service result.  This is typically used to perform complex validation or to
extract values from the result for use in subsequent services.

- ``Postprocessing Mode`` Control whether or not the ``Postprocessing`` script is executed

  - ``Always run`` (**default**) The ``Postprocessing`` script will execute for each device
  - ``Run on success only``
  - ``Run on failure only``

- ``PostProcessing`` A python script to inspect or update the current result.

  - Variable **results**

    - Contains the full results dictionary for the current device, exactly as seen in the results view.

      - Changes to this dictionary are reflected in the final result of the service.

    - **results["success"]** The overall service status.
    - **results["result"]** The resulting data from running the service.

  - See `Using python code in the service panel`_ for the full list of variables and functions.


Validation
""""""""""

Validation can consist of:
  - Text matching: looking for a string in the result, or matching the result against a regular expression.
  - Dictionary matching: check that a dictionary is included or equal to the result.
  - Anything else: you can use python code to change the result, including the value of the ``success`` key.

- ``Conversion Method`` The type of automatic conversion to perform on the service result.

  - ``No conversion`` (default) Use the result with no modification.
  - ``Text`` Convert the result to a python string.
  - ``JSON`` Convert a string representing JSON data to a python dictionary.
  - ``XML`` Convert a string representing XML data to a python dictionary.

- ``Validation Method`` The validation method depends on whether the result is a string or a dictionary.

  - ``No validation`` No validation is performed
  - ``Text match`` Matches the result against ``Content Match`` (string inclusion, or regular expression if
    ``Match content against Regular expression`` is selected)
  - ``dictionary Equality`` Check for equality against the dictionary provided in ``Dictionary Match``
  - ``dictionary Inclusion`` Check that all ``key`` : ``value`` pairs from the dictionary provided in ``Dictionary Match``
    can be found in the result.

- ``Negative Logic`` Reverses the ``success`` boolean value in the results: the result is inverted: a success
  becomes a failure and vice-versa. This prevents the user from using negative look-ahead regular expressions.
- ``Delete spaces before matching`` (``Text`` match only) All whitespace is stripped from both the output and
  ``Content Match`` before comparison to prevent these differences from causing the match to fail.

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
- ``Mail recipients`` Must be a list of email addresses, separated by comma.
- ``Display only failed nodes`` the notification will not include devices for which the service ran successfully.

To set up the mail system, you must set the variable of the ``mail`` section in the settings.
``server``, ``port``, ``use_tls``, ``username``, ``sender``, ``recipients``.
Besides, you must set the password via the ``MAIL_PASSWORD`` environment variable.

The ``Mail Recipients`` parameter must be set for the mail system to work; the `Admin / Administration` panel parameter can
also be overriden from Step2 of the Service Instance and Workflow configuration panels. For Mail notification, there is
also an option in the Service Instance configuration to display only failed objects in the email summary versus seeing a
list of all passed and failed objects.

In Mattermost, if the ``Mattermost Channel`` is not set, the default ``Town Square`` will be used.


Using python code in the service panel
--------------------------------------

There are two types of field in the service panel where the user is allowed to use pure python code:
substitution fields (light blue background) and python fields (light red background).
In these fields, you can use any python code, including a number of **variables** that are made available
to the user.

Variables
*********

- ``device``

  - **Meaning**: this is the device on which the service is running.
  - **Type** Database Object.
  - **Available**: when the service is running on a device.

- ``devices``

  - **Meaning**: the full list of devices for the service.
  - **Type**: List of database objects.
  - **Available**: Always.

- ``get_result`` (see :ref:`get_result`)

  - **Meaning**: Fetch the result of a service in the workflow that has already been executed.
  - **Type** Function.
  - **Return Type** Dictionary
  - **Available**: when the service runs inside a workflow.
  - **Parameters**:

    - ``service`` (**mandatory**) Name of the service
    - ``device`` (**optional**) Name of the device, when you want to get the result of the service for a
      specific device.
    - ``workflow`` (**optional**) If your workflow has multiple subworkflows, you can specify
      a subworkflow to get the result of the service for a specific subworkflow.

- ``get_var``

  - **Meaning**: Retrieve a value by ``name`` that was previously saved in the workflow.  Use ``set_var`` to save values.  Always
    use the same ``device`` and/or ``section`` values with ``get_var`` that were used with the original ``set_var``.

  - **Type** Function.
  - **Return Type** None
  - **Available**: always.
  - **Parameters**:

    - ``name`` Name of the variable
    - ``device`` (**optional**) The value is stored for a specific device.
    - ``section`` (**optional**) The value is stored in a specific "section".

- ``log``
  - **Meaning**: Write a
  - **Type**:
  - **Return Type**: None
  - **Available**: always.
  - **Parameters**:

    - **severity**: (**string**) Valid values in escalating priority order: **info**, **warning**, **error**, **critical**.
    - **message**: (**string**) Verbiage to be logged.
    - **device**: (**string**, **optional**) Associate log message to a specific device.
    - **app_log**: (**boolean**, **optional**) Write log message to application log in addition to custom logger.
    - **logger**: (**string**, **optional**) When specified, the log message is written to the named custom logger
      instead of the application log. Set **app_log** = True to send log message to both the custom and application logs.
      Contact the administrator to create a custom logger, if needed.

- ``parent_device``

  - **Meaning**: parent device used to compute derived devices.
  - **Type** Database Object.
  - **Available**: when the iteration mechanism is used to compute derived devices.

- ``result``

  - **Meaning**: this is the result of the current service.
  - **Type** Dictionary.
  - **Available**: after a service has run.

- ``set_var``

  - **Meaning**: Save a value by ``name`` for use later in a workflow.  When ``device`` and/or ``section`` is specified, a unique
    value is stored for each combination of device and section.  Use ``get_var`` for value retrieval.
  - **Type** Function.
  - **Return Type** None
  - **Available**: always.
  - **Parameters**:

    - ``name`` Name of the variable
    - ``device`` (**optional**) The value is stored for a specific device.
    - ``section`` (**optional**) The value is stored in a specific "section".

Variables saved globally (i.e. set_var("var1", value) and for a device (i.e. set_var("var2", device=device.name)) are
made available within every Python code can be used.  Only device specific variables for the current device are
available.  Device specific variables override global variables of the same name.

- ``settings``

  - **Meaning**: eNMS settings, editable from the top-level menu.
    It is initially set to the content of ``settings.json``.
  - **Type** Dictionary.
  - **Available**: Always.

- ``send_email`` lets you send an email with optional attached file. It takes the following parameters:

  - ``title`` (mandatory, type ``string``)
  - ``content`` (mandatory, type ``string``)
  - ``sender`` (optional, type ``string``) Email address of the sender. Default to the sender address
    of eNMS settings.
  - ``recipients`` (optional, type ``string``) Mail addresses of the recipients, separated by comma.
    Default to the recipients addresses of eNMS settings.
  - ``reply_to`` (optional, type ``string``) Single mail address for replies to notifications
  - ``filename`` (optional, type ``string``) Name of the attached file.
  - ``file_content`` (optional, type ``string``) Content of the attached file.

  .. code::

    send_email(
        title,
        content,
        sender=sender,
        recipients=recipients,
        reply_to=reply_to,
        filename=filename,
        file_content=file_content
    )

- ``workflow``

  - **Meaning**: current workflow.
  - **Type** Database Object.
  - **Available**: when the service runs inside a workflow.

Substitution fields
*******************

Substitution fields, marked in the interface with a light blue background, lets you include python code
inside double curved brackets (``{{your python code}}``).
For example, the URL of a REST call service is a substitution field. If the service is running on device
targets, you can use the global variable ``device`` in the URL.
When the service is running, eNMS will evaluate the python code in brackets and replace it with its value.
See `Using python code in the service panel`_ for the full list of variables and functions available within substitution
fields.

.. image:: /_static/automation/services/variable_substitution.png
   :alt: Variable substitution
   :align: center

Running the service on two devices ``D1`` and ``D2`` will result in sending the following GET requests:

.. code::

  "GET /rest/get/device/D1 HTTP/1.1" 302 219
  "GET /rest/get/device/D2 HTTP/1.1" 302 219


Python fields
*************

Python fields, marked with a light red background, accept valid python code.

- In the ``Device Query`` field of the "Devices" section of a service. An expression that evaluates to an iterable
  containing the name(s) or IP address(es) of the desired inventory devices.
- In the ``Skip Service if True`` field of the "Workflow" section of a service.  The expression result is treated as a boolean.
- In the ``Query`` field of the Variable Extraction Service.  The expression result is used as the extracted value.
- In the code of a Python Snippet Service, or the ``Preprocessing`` and ``Postprocessing`` field on every service.

.. _Custom Services:

Custom Services
---------------

In addition to the services provided by default, you are free to create your own services.
When the application starts, it loads all python files in ``eNMS / eNMS / services`` folder.
If you want your custom services to be in a different folder, you can set a different path in the
``settings``, section ``paths``.
Creating a service means adding a new python file in that folder.
You are free to create subfolders to organize your own services any way you want:
eNMS will automatically detect them.
Just like all other services, this python file must contain a model and a form.
After adding a new custom service, you must reload the application before it appears in the web UI.

Running a service
-----------------

You can run a service from the "Services" page ("Run" button) or from the "Workflow Builder"
(right-click menu).

There are two types of runs:

- Standard run: uses the service properties during the run.
- Parameterized run: a window is displayed with all properties initialized to the service

properties. You can change any property for the current run, but these changes won't be saved
back to the service properties.

Results
*******

A separate result is stored for each run of a service / workflow, plus a unique result for every device and for every
service and subworkflow/superworkflow within a workflow.
Each result is displayed as a JSON object. If the service is run on several devices, you can display the results for a
specific device, or display the list of all "failed" / "success" device.
In the event that retries are configured, the results dictionary will contain an overall results section,
as well as a section for each attempt, where failed and retried devices are shown in subsequent sections
starting with attempt2.
