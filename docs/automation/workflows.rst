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

- Section 2: edit and duplicate the current workflow, create a new workflow, add existing services to the workflow,
create labels, skip or unskip services, and delete selected services and edges.
- Section 3: run or pause a workflow, and display the workflow logs and results.
- Section 4: refresh the workflow, zoom and unzoom, move to the previous or next workflow, and move to the selected
  subworkflow.
- Section 5: choose which workflow to display, and which results.

Some of these actions are also available from the right-click menus (clicking on the background, on a service or on an
edge generate different menus).

Workflow Devices
----------------

The devices used when running a workflow depend on the workflow ``Run Method`` that you can configure in the edit panel,
section ``Devices``.
There are three run methods for a workflow:

- **device by device**: the devices configured **at workflow level** are considered. The workflow will run for
  each device independently from the other devices. With multiprocessing disabled, devices will run the workflow 
  **sequentially**, one at a time. If multiprocessing **at workflow level** is enabled, you can have as many
  devices running the workflow in parallel as you have available processes.
- **service by service using workflow targets**: the devices configured **at workflow level** are considered.
  Each device can follow a different path depending on whether a service is successful or not, but services are always
  run **one at a time**. eNMS will compute the targets of a service by keeping track of the path of each device
  throughout the workflow. Multiprocessing must be enabled **at service level**.
- **service by service using service targets**: only the devices selected **at the individual service level**
  are considered. Devices selected at workflow level are ignored. A service is considered successful if it ran
  successfully on all of its targets (if it fails on at least one target, it is considered to have failed).
  This mode is useful for workflows where services have different targets

For the first two modes, devices are independent from each other: one device may run on all services in the workflow
if it is successful while another one could stop at the first step: they run the workflow independently and will likely
follow different paths in the workflow depending on whether they fail or pass services thoughout the workflow.

Connection Cache
----------------

When using netmiko and napalm services in a workflow, eNMS will cache and reuse the connection automatically.
In the ``Specifics`` section of a service, there are two properties to change this behavior :

- ``Start New Connection``: **before the service runs**, the current cached connection is discarded and a new one
  is started.
- ``Close Connection``: once the service is done running, the current connection will be closed.

Workflow Restartability
-----------------------

A workflow can be restarted with any services set as "Entry points"
and with the payload from a previous runs.
This is useful if you are testing a workflow with a lot of services, and you don't want it to
restart from scratch all the time.

You must click on "Run with Updates" and go to the "Workflow" section to access these parameters.

.. image:: /_static/automation/workflows/workflow_restartability.png
   :alt: Workflow Restartability
   :align: center

Waiting times
-------------

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

Service dependency
------------------

If a service ``A`` must be executed before a service ``B`` in the workflow, eNMS must be made aware of that dependency by creating a  ``Prerequisite`` edge.

In the example below, the service ``process_payload1`` uses the results from ``get_facts`` and ``get_interfaces``. By creating two prerequisite edges (from ``get_facts`` to ``process_payload1`` and from ``get_interfaces`` to ``process_payload1``), we ensure that eNMS will not run ``process_payload1`` until both ``get_interfaces`` and ``get_config`` have been executed.

.. image:: /_static/automation/workflows/payload_transfer_workflow.png
   :alt: Payload Transfer Workflow
   :align: center

Payload transfer
----------------

The most important characteristic of workflows is the transfer of data between services.
When a service starts, it is provided with the results of ALL services in the workflow
that have already been executed (and not only the results of its "predecessors").

In case the job has "device targets", it will receive an additional argument ``device``

::

    def job(self, payload: dict, device: Device) -> dict:
        return {"success": True, "result": "example"}

The first argument of the ``job`` function is ``payload``: it is a dictionary that
contains the results of all services that have already been executed.

If we consider the aforementioned workflow, the job ``process_payload1`` receives
the variable ``payload`` that contains the results of all other services in the workflow
(because it is the last one to be executed).

It can access the results with the ``get_result`` function, that takes two arguments:

- service (mandatory): the name of the service whose result you want to retrieve
- device (optional): if the service has device targets, you can specify 
    a device in case you want to get the result of the service for a specific device.

::

    def get_result(self, service: str, device: Optional[str] = None) -> dict:
        ...
        return result

You should access the result of previous services with the ``get_result`` function.
Examples:

- ``get_result("get_facts")``
- ``get_result("get_interfaces", device="Austin")``
- ``get_result("get_interfaces", device=device.name)``

You can use the ``get_result`` function everywhere python code is accepted.
See the "Advanced / python code" section of the docs for more information.

Saving and retrieving values in a workflow
------------------------------------------

You can define variables in the payload with the ``set_var`` function, and retrieve data from the payload with the ``get_var`` function. 
``set_var`` takes the following arguments:

- the variable name (first argument)
- the value to be stored (second argument)
- Keyword argument device: A unique value will be stored for each device.
- Keyword argument section: A unique value will be stored for each section.

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


Use data from a previous service in the workflow
--------------------------------------------

If a service "B" needs to use the results from a previous service "A", it can access the results of service "A"
with the ``get_result`` function.
The ``get_result`` function takes two arguments:

- the name of the service (name of the service or workflow whose results you want to retrieve)
- (Optional) the name of a device, if you want to retrieve the service results for a specific device.

Example: ``get_result("Payload editor", device="Test_device")``

The results of a service is always a dictionary: this is what the ``get_result`` function returns.
You can therefore treat it as a dictionary to access the content of the results:

``get_result("Payload editor")["runtime"]``

Use of a SwissArmyKnifeService instance to process the payload
--------------------------------------------------------------

When the only purpose of a function is to process the payload to build a "result" set
or simply to determine whether the workflow is a "success" or not,
the service itself does not have have any variable "parameters".
It is not necessary to create a new Service (and therefore a new class, in a new file)
for each of them. Instead, you can group them all in the SwissArmyKnifeService class,
and add a method called after the name of the instance.
The SwissArmyKnifeService class acts as a "service multiplexer"
(see the ``SwissArmyKnifeService`` section of the doc).
If we want to use the results of the Napalm getters in the final service ``process_payload1``, here's what the function of ``process_payload1`` could look like:

::

    def process_payload1(self, run: "Run", payload: dict, device: Device) -> dict:
        # we use the name of the device to get the result for that particular device.
        get_facts = run.get_result("get_facts", device.name)
        get_interfaces = run.get_result("get_interfaces", device.name)
        uptime_less_than_50000 = get_facts["result"]["get_facts"]["uptime"] < 50000
        mgmg1_is_up = get_interfaces["result"]["get_interfaces"]["Management1"]["is_up"]
        return {
            "success": True,
            "uptime_less_5000": uptime_less_than_50000,
            "Management1 is UP": mgmg1_is_up,
        }


This ``job`` function reuses the results of the Napalm getter ``get_facts`` (which is not a direct predecessor of ``process_payload1``) to create new variables and inject them in the results.
From the web UI, you can then create an Service Instance of ``SwissArmyKnifeService`` called ``process_payload1``, and add that instance in the workflow. When the service instance is called, eNMS will automatically use the ``process_payload1`` method, and process the payload accordingly.

.. tip:: You can run a service directly from the Workflow Builder to see if it passes (and rerun if it fails), and also which payload the service returns.

Python code
-----------

There are a number of places in the GUI where the user is allowed to use pure python code:

- Inside double curved brackets in the service parameters (``{{python expression}}``). This is called "Variable substitution" (fields that support variable substitution are marked with a light blue background).
- In the ``Device Query`` field of the "Devices" section of a service. This field lets the user define the targets of a service programmatically.
- In the ``Skip Service If Python Query evaluates to True`` field of the "Workflow" section of a service. This field lets the user define whether or not a service should be skipped programmatically.
- In the ``Query`` field of the Variable Extraction Service.
- In the code of a Python Snippet Service.

You have access to the following variables:

- ``device``: current device, if the ``Has Device Targets`` is ticked ("device" object).
- ``payload``: current state of the workflow payload (dictionary).
- ``config``: eNMS global configuration (available in the administration panel, section "Parameters", button "General").
- ``workflow``: parent workflow, if the service is running within a workflow.
- ``parent_device``: available only when derived devices are defined using a Python Query.

And the following functions:

- ``get_var`` and ``set_var``: function to save data to and retrieve data from the payload.
    The use of these two functions is explained in the section ""Set and get data in a workflow" of the workflow payload docs.
- ``get_result``: function to retrieve a result for a given service (and for an optional device).
    The use of this function is described in the section "Use data from a previous service in the workflow" of the workflow payload docs.