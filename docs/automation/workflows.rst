===============
Workflow System
===============

A workflow is a graph of services connected with ``success`` and ``failure`` edges.
Each service returns a ``success`` boolean value that indicates whether it ran successfully or not.
If a service is executed successfully, the workflow continues down the ``success`` path to the next service, otherwise
it goes down the ``failure`` path.
Workflows are created and managed from the :guilabel:`Workflow Builder`.

Workflow Management
-------------------

In the :guilabel:`Automation / Workflow Management` page, click on the button ``Create`` and fill the workflow creation form.
The new workflow will be automatically added to the table of workflows.
From the same page, workflows can be edited, deleted, and duplicated. They can also be ran, and their result logs examined.

.. image:: /_static/automation/workflows/workflow_management.png
   :alt: Workflow management
   :align: center

Workflows can also be created from the Workflow Builder page.

Workflow Builder
----------------

The :guilabel:`Automation/Workflow Builder` is the place where services (or other workflows) are organized into workflows.
It contains:

- A drop-down list containing all existing workflows. This list allows switching between workflows.
- The workflow itself is displayed as a graph. The  services are connected by arrows of type success edge or failure edge.
- A ``general right-click menu`` can be accessed by clicking on the background or white-space.
- A ``service-specific right-click menu`` can be accessed by right clicking on a specific service.

The ``general right-click menu`` contains the following entries:

- Change Mode (create edges or move a service in the Workflow Builder)
- Create Workflow
- Add to Workflow (lets you choose which services to add amongst all existing services)
- Run Workflow (starts the workflow)
- Edit Workflow (same Workflow editor from the Workflow Management page)
- Workflow Results
- Workflow Logs
- Refresh View

.. image:: /_static/automation/workflows/workflow_background_menu.png
   :alt: Workflow management
   :align: center

From the ``service-specific right-click menu``, you can:

- Edit a service (service or workflow)
- Run a service (service or workflow)
- Display the Results
- Delete a service (remove from the workflow)

.. image:: /_static/automation/workflows/workflow_service_menu.png
   :alt: Workflow management
   :align: center

Waiting time
------------

Services and Workflows have a ``Waiting time`` property: this tells eNMS how much time it should wait after the Service/Subworkflow has run before it begins the next service.
This is useful if the service you're running needs time to be processed or operated upon before another service can be started.

A service can also be configured to "retry"  if the results returned are not as designed. An example execution of a service in a workflow, in terms of waiting times and retries, is as follows:

::

  First try
  time between retries pause
  Retry 1
  time between retries pause
  Retry 2  (Successful, or only 2 Retries specified)
  Waiting time pause

Workflow devices
----------------

When you create a workflow, just like with services instances, the form will also contain multiple selection fields for you to select "target devices", as well as an option ``Use Workflow Targets``:

- If selected, the devices for the workflow will be used for execution.
- If not selected, the devices selected at the individual service level will be used for execution.


If ``Use Workflow Targets`` is unticked, services will run on their own targets. A service is considered successful if it ran successfully on all of its targets (if it fails on at least one target, it is considered to have failed).
The "Use service targets" mode can be used for workflows where services have different targets (for example, a first service would run on devices A, B, C and the next one on devices D, E).

If ``Use Workflow Targets`` is ticked, the workflow will run on its own targets (all devices configured at service level are ignored). Devices are independent from each other: one device may run on all services in the workflow if it is successful while another one could stop at the first step: they run the workflow independently and will likely follow different path in the workflow depending on whether they fail or pass services thoughout the workflow.

Connection Cache
----------------

When using several netmiko and napalm connections in a workflow, the connection object is cached and reused automatically.
If for some reason you want a service to create a fresh connection, you can tick the ``Start New Connection`` box
in the "Workflow" section of the creation panel.
Upon running this service, eNMS will automatically discard the current cached connection, start a new one and
make it the new cached connection.

Success of a Workflow
---------------------

The behavior of the workflow is such that the workflow is considered to have an overall Success status if the END service is reached. So, the END service should only be reached by an edge when the overall status of the workflow is considered successful. If a particular service service fails, then the workflow should just stop there (with the workflow thus having an overall Failure status), or it should call a cleanup/remediation service (after which the workflow will just stop there).

Position saving
---------------

Note that the positions of the services of a workflow in the Workflow Builder page is saved to the database only when the user navigates away from the workflow.
- Upon leaving the Workflow Builder page.
- When switching to another workflow.

All other changes to the Workflow Builder are saved immediately.

Automatic refresh
-----------------

A workflow displayed in the Workflow Builder page is automatically updated:
- Every 0.7 second if the workflow is currently running
- Every 15 seconds otherwise

This allows multiple users to work concurrently on a single Workflow in the Workflow Builder.

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

The base code for a job function is the following:

::

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


The dictionary that is returned by ``job`` is the result of the job,
i.e the information that will be transferred to the next jobs to run in the workflow.
It MUST contain a key ``success``, to tell eNMS whether the job was considered a
success or not (therefore influencing how to move forward in the workflow:
either via a ``Success`` edge or a ``Failure`` edge).

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