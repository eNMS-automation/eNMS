========
Services
========

A service is a Python script that performs an action. A service is defined by:

- A **model** class: the service parameters, and what the service is doing via a ``job`` function.
- A **form** class: the different fields eNMS displays in the UI, and their corresponding validation.

eNMS comes with a number of "default" services based on network automation frameworks such as
``netmiko``, ``napalm`` and ``ansible``, but you are free to create your own services.
Each service will return a python dictionary as a result. This dictionary will always contains
a ``success`` boolean value that indicates whether it ran successfully or not.

All services are displayed in :guilabel:`Automation / Services`, where you can create new services and
edit, duplicate, delete, and run existing ones.

.. image:: /_static/automation/services/services.png
   :alt: Service Management page
   :align: center

.. note::

  You can also export services: this creates a YAML file with all service properties in the
  ``files / exported_services`` directory.
  This allows migrating services from one VM to another if you are using multiple VMs.

Service Panel
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
- ``Skip Service if True`` This fields expect a python code that will evaluates to either ``True``
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

The validation can consist in:
  - Text matching: looking for a string in the result, or matching the result against a regular expression.
  - Dictionary matching: check that a dictionary is included or equal to the result.
  - Anything else: you can use python code to change the result, including the value of the ``success`` key.

- ``Conversion Method`` (default: ``No conversion``) Some services will fetch a result from an external source.
  There are three conversion modes:

  - ``Text`` Convert the result to a python string.
  - ``JSON`` Convert a string representing JSON data to a python dictionary.
  - ``XML`` Convert a string representing XML data to a python dictionary.

- ``Validation Method`` The validation method depends on whether the result is a string or a dictionary.

  - ``Text match`` Matches the result against ``Content Match`` (string inclusion, or regular expression if 
    ``Match content against Regular expression`` is selected)
  - ``dictionary Equality`` Check for equality against the dictionary provided in ``Dictionary Match``
  - ``dictionary Inclusion`` Check for dictionary inclusion, in the sense that all ``key`` : ``value``
    pairs from the dictionary provided in ``Dictionary Match`` can be found in the result.

- ``Negative Logic`` Reverses the ``success`` boolean value in the results: the result is inverted: a success
  becomes a failure and vice-versa. This prevents the user from using negative look-ahead regular expressions.
- ``Delete spaces before matching`` (``Text`` match only) The output is stripped from all spaces and newlines.
  in the result and ``Content Match`` (they can cause the match to fail)

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

- ``result``

  - **Meaning**: this is the result of the current service.
  - **Type** Dictionary.
  - **Available**: after a service has run.

- ``config``

  - **Meaning**: eNMS configuration, editable from :guilabel:`Admin / Administration`, button
    ``Configuration``. It is initially set to the content of ``config.json``.
  - **Type** Dictionary.
  - **Available**: Always.

- ``parent_device``

  - **Meaning**: Parent device used to compute derived devices.
  - **Type** Database Object.
  - **Available**: when the iteration mechanism is used to compute derived devices.

- ``workflow`` (only in a **workflow**)

  - **Meaning**: current workflow.
  - **Type** Database Object.
  - **Available**: when the service runs inside a workflow.

- ``get_result`` (only in a **workflow**, see :ref:`get_result`)

  - **Meaning**: Fetch the result of a service in the workflow that have already been executed.
  - **Type** Function.
  - **Return Type** Dictionary
  - **Available**: when the service runs inside a workflow.
  - **Parameters**:

    - ``service`` (**mandatory**) Name of the service
    - ``device`` (**optional**) Name of the device, when you want to get the result of the service for a
      specific device.
    - ``workflow`` (**optional**) If your workflow has multiple subworkflows, you can specify
      a device in case you want to get the result of the service for a specific device.

- ``set_var`` **(only in a workflow)**

  - **Meaning**: Save a variable in the workflow payload for later.
  - **Type** Function.
  - **Return Type** None
  - **Available**: when the service runs inside a workflow.
  - **Parameters**:

    - First argument: Name of the variable
    - Second argument: Value
    - ``device`` (**optional**) The value is stored for a specific device.
    - ``section`` (**optional**) The value is stored in a specific "section".

- ``app.send_email`` lets you send an email with optional attached file. It takes the following parameters:

  - ``title`` (mandatory, type ``string``)
  - ``content`` (mandatory, type ``string``)
  - ``sender`` (optional, type ``string``) Email address of the sender. Default to the sender address
    of eNMS configuration.
  - ``recipients`` (optional, type ``string``) Mail addresses of the recipients, separated by comma.
    Default to the recipients addresses of eNMS configuration.
  - ``filename`` (optional, type ``string``) Name of the attached file.
  - ``file_content`` (optional, type ``string``) Content of the attached file.

  .. code::

    app.send_email(
        title,
        content,
        sender=sender,
        recipients=recipients,
        filename=filename,
        file_content=file_content
    )

Substitution fields
*******************

Substitution fields, marked in the interface with a light blue background, lets you include python code
inside double curved brackets (``{{your python code}}``).
For example, the URL of a REST call service is a substitution field. If the service is running on device
targets, you can use the global variable ``device`` in the URL.
When the service is running, eNMS will evaluate the python code in brackets and replace it with its value.

.. image:: /_static/automation/services/variable_substitution.png
   :alt: Variable substitution
   :align: center

Running the service on two devices ``D1`` and ``D2`` will result in sending the following GET requests:

.. code::

  "GET /rest/get/device/D1 HTTP/1.1" 302 219
  "GET /rest/get/device/D2 HTTP/1.1" 302 219


Python fields
*************

Python fields, marked with a light red background, accept pure python code only.

- In the ``Device Query`` field of the "Devices" section of a service. This field lets the user define the targets of a service programmatically.
- In the ``Skip Service if True`` field of the "Workflow" section of a service. This field lets the user define whether or not a service should be skipped programmatically.
- In the ``Query`` field of the Variable Extraction Service.
- In the code of a Python Snippet Service.

.. _Custom Services:

Custom Services
---------------

In addition to the services provided by default, you are free to create your own services.
When the application starts, it loads all python files in ``eNMS / eNMS / services`` folder.
If you want your custom services to be in a different folder, you can set a different path in the
:ref:`Configuration`, section ``paths``.
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

Results are stored for each run of the service / workflow.
The results are displayed as a JSON object. If the service ran on several device, you can display the results for a
specific device, or display the list of all "failed" / "success" device.
In the event that retries are configured, the Logs dictionary will contain an overall results section,
as well as a section for each attempt, where failed and retried devices are shown in subsequent sections
starting with attempt2.