===============
Workflow System
===============

A workflow is a graph of services connected with ``success`` and ``failure`` edges.
If a service is executed successfully, the workflow continues down the ``success`` path to the next service,
otherwise it goes down the ``failure`` path. A workflow is considered to have run successfully if the "End"
service is reached.
Workflows are managed from the :guilabel:`Workflow Builder`.
When a workflow is running, the results are automatically updated in real-time in the workflow builder.

Workflow Builder
----------------

.. image:: /_static/automation/workflows/workflow_builder.png
   :alt: Workflow builder
   :align: center

- Section 1: services and edges creation.

    - The first row lets you choose a service type and click on the "plus" button to create a new service that
      will be added to the workflow.
    - On the second row, you can change the mode to "Edge creation" and select which type of edge you want to create.

- Section 2: edit and duplicate the current workflow, create a new workflow, add existing services to the
  workflow, create labels, skip or unskip services, and delete selected services and edges.
- Section 3: run or pause a workflow, and display the workflow logs and results.
- Section 4: refresh the workflow, zoom and unzoom, move to the previous or next workflow, and move to the
  selected subworkflow.
- Section 5: choose which workflow to display, and which results.

.. note::

  Some of these actions are also available from the right-click menus (clicking on the background, on a service
  or on an edge generate different menus).

Workflow Devices
----------------

The devices used when running a workflow depend on the workflow ``Run Method`` that you can configure in the
edit panel, section ``Devices``.
There are three run methods for a workflow:

Device by device
****************

  - Uses the devices configured at **workflow** level.
  - Multiprocessing must be enabled at **workflow** level.
  - Workflow will run for each device independently, one at a time if multiprocessig is disabled
    in parallel otherwise.

Service by service using workflow targets
*****************************************

  - Uses the devices configured at **workflow** level.
  - Multiprocessing must be enabled at **service** level.
  - The workflow will run one service at a time, but each device can follow a different path depending on
    the results of each service for that device.

Service by service using service targets
****************************************

  - Uses the devices configured at **service** level.
  - Multiprocessing must be enabled at **service** level.
  - The workflow will run one service at a time. A service is considered successful if it ran successfully
    on all of its targets (if it fails on at least one target, it is considered to have failed).

Transfer of data among services
-------------------------------

Using the result of previous services
*************************************

When a service starts, you can have access to the results of all services in the workflow that have already
been executed with a special function called ``get_result``. The result of a service is the dictionary that is
returned by the ``job`` function of the service, and calling ``get_result`` will return that dictionary.
There are two types of results: top-level and per-device. If a service runs on 5 devices, 6 results will be
created: one for each device and one top-level result for the service itself.

- ``service`` (**mandatory**) Name of the service
- ``device`` (**optional**) Name of the device, when you want to get the result of the service for a
  specific device.
- ``workflow`` (**optional**) If your workflow has multiple subworkflows, you can specify
  a device in case you want to get the result of the service for a specific device.

Examples:

- ``get_result("get_facts")`` Get the top-level result for the service ``get_facts``
- ``get_result("get_interfaces", device="Austin")`` Get the result of the device ``Austin`` for
  ``get_interfaces``
- ``get_result("get_interfaces", device=device.name)`` Get the result of the current device for
  ``get_interfaces``
- ``get_result("Payload editor")["runtime"]`` Get the ``runtime`` key of the top-level result of the
  ``Payload editor`` service.

The ``get_result`` function everywhere python code is accepted.

Saving and retrieving values in a workflow
------------------------------------------

You can define variables in the payload with the ``set_var`` function, and retrieve data from the payload
with the ``get_var`` function.

``set_var`` takes the following arguments:

- First argument: Name of the variable
- Second argument: Value
- ``device`` (**optional**) A unique value will be stored for each device.
- ``section``(**optional**) Store the value in a separate "section".

Variables can be scoped in different ways: global, per-device, user-defined,
and a combination of per-device and user-defined.
When no device or section is specified, the variable stores a single global value.
Specifying a device or section saves a unique value for the device or section.
Specifying both a device and section stores a unique value for each combination
of device and section.

For example, let's consider the following python snippet:

::

  set_var("global_variable", value=1050)
  set_var("variable", "variable_in_variables", section="variables")
  set_var("variable1", 999, device=device.name)
  set_var("variable2", "1000", device=device.name, section="variables")
  set_var("iteration_simple", "192.168.105.5", section="pools")
  devices = ["Boston", "Cincinnati"] if device.name == "Chicago" else ["Cleveland", "Washington"]
  set_var("iteration_device", devices, section="pools", device=device.name)

Miscellaneous
-------------

Service dependency
******************

If a service must be run after another service, you can force that order by creating a ``Prerequisite`` edge.
In the example below, the service ``process_payload1`` uses the results from ``Get Facts`` and
``Get Interfaces``. By creating two prerequisite edges, we ensure that ``process_payload1`` will not be run
until both ``Get Facts`` and ``Get Interfaces`` have been executed.

.. image:: /_static/automation/workflows/service_dependency.png
   :alt: Service Dependency
   :align: center

Workflow Restartability
***********************

A workflow can be restarted with any services set as "Entry points"
and with the payload from a previous runs.
This is useful if you are testing a workflow with a lot of services, and you don't want it to
restart from scratch all the time.

Connection cache
****************

When using netmiko and napalm services in a workflow, eNMS will cache and reuse the connection automatically.
In the ``Specifics`` section of a service, there are two properties to change this behavior :

- ``Start New Connection``: **before the service runs**, the current cached connection is discarded and a new one
  is started.
- ``Close Connection``: once the service is done running, the current connection will be closed.

Waiting times
*************

Services and Workflows have a ``Waiting time`` property: this tells eNMS how much time it should wait after
the service has run before it begins the next service.

A service can also be configured to "retry"  if the results returned are not as designed.
An example execution of a service in a workflow, in terms of waiting times and retries, is as follows:

::

  First try
  time between retries pause
  Retry 1
  time between retries pause
  Retry 2  (Successful, or only 2 Retries specified)
  Waiting time pause
