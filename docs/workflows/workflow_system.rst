===============
Workflow System
===============

A workflow is a directed graph whose nodes can be a service or another workflow.

Each job in eNMS returns a boolean value:
  - ``True`` if it ran successfully.
  - ``False`` otherwise.

There are two types of edge in a workflow: ``Success`` edge and ``Failure`` edge.
The ``success edge`` indicates where to move in the graph if the source job was executed with success, while the ``failure edge`` takes a different path in case of failure.
Additionally, each workflow must have a ``Start`` job and an ``End`` job for eNMS to know which job should be executed first and when to stop running the workflow.

Workflows are created and managed from the :guilabel:`Automation/Workflow Management` page.

Workflow Management
-------------------

In the :guilabel:`Automation/Workflow Management` page, click on the button ``Add a new workflow`` and fill the workflow creation form.
The new workflow will be automatically added to the table of workflows.
From the same page, workflows can be edited, deleted, and duplicated. They can also be ran, and their result logs examined.

.. image:: /_static/workflows/workflow_system/workflow_management.png
   :alt: Workflow management
   :align: center

Workflow Builder
----------------

The :guilabel:`Automation/Workflow Builder` is the place where services (or other workflows) are organized into workflows.
It contains:
  - A drop-down list containing all existing workflows that allows switching between workflows.
  - The workflow itself, displayed as a graph. The nodes are ``jobs`` (services or workflows), and there are two types of edges: ``Success`` edge and ``Failure`` edge. If a job runs successfully, it will "follow" the ``success`` edge, otherwise the ``failure`` edge.
  - A ``general right-click menu`` (Right-click on the background).
  - A ``job-specific right-click menu`` (Right-click on a job).

The ``general right-click menu`` contains the following entries:
  - Change Mode (create edges or move a job in the Workflow Builder)
  - Add Service or Workflow (lets you choose a job to add amongst all existing jobs)
  - Run Workflow (starts the workflow)
  - Edit Workflow (same Workflow editor from the Workflow Management page)
  - View and compare the logs of the workflow (``Workflow Logs``, ``Compare Workflow Logs``)
  - Refresh View

.. image:: /_static/workflows/workflow_system/workflow_background_menu.png
   :alt: Workflow management
   :align: center

From the ``job-specific right-click menu``, you can:
  - Edit a job (service or workflow)
  - Run a job (service or workflow)
  - View and compare the logs of the job (``Job Logs``, ``Compare Job Logs``)
  - Delete a job (service or workflow)

.. image:: /_static/workflows/workflow_system/workflow_job_menu.png
   :alt: Workflow management
   :align: center

Waiting time
------------

Services and Workflows have a ``Waiting time`` property: this tells eNMS how much time it should wait after the Service/Subworkflow has run.
This is useful if for example you're reloading a device: you'll need to wait some time for the device to come back to life before moving on.
Another use-case is to run an asynchronous command that takes some time to be executed. For example, on Cisco devices, deleting a VRF can take up to a few minutes.

If a script is configured to "retry" in case it is not successful, eNMS will also wait "time between retries" between each try. The execution of the service in a workflow, in terms of waiting times, would be the following:

::

  First try
  time between retries pause
  Retry 1
  time between retries pause
  Retry 2
  Waiting time pause

Workflow devices
----------------

When you create a workflow, just like with services instances, the form will also contain multiple selection fields for you to select "target devices". If you don’t select any device, the devices for each Service (or sub- Workflow) will be used. If you select target devices for the workflow, all devices selected at the individual Service level will be ignored, and the workflow will run only on the devices selected for the workflow.

Both services and workflows have a property ``Multiprocessing``:
  - If Multiprocessing is disabled at the workflow level, and devices have been selected at workflow level, the workflow will run on each device sequentially (device after device). Devices configured at service level are ignored.
  - If Multiprocessing is enabled at the workflow level, and devices have been selected at workflow level, the workflow will run independently and in parallel on each of the selected devices (given that the max number of processes is not exceeded). Each device will run its own independent copy of the workflow regardless of the status of the other devices. Devices configured at service level are also ignored.
  - If devices are selected at service level (and no devices selected at workflow level), and the service level Multiprocessing property is disabled, each service will run on its own selected devices sequentially (device after device), and note that the device list for each service may be different. In this case, the workflow level 'Multiprocessing' parameter is ignored.
  - If devices are selected at service level (and no devices selected at workflow level), and the service level Multiprocessing property is enabled, each device for a given service will run in parallel to the other devices (all selected devices running at the same time), but the workflow will stop and wait for all devices to have finished the service job before moving on to the next service in the workflow. In this case, the workflow level 'Multiprocessing' parameter is ignored.

It is important to note that if you don't select any device at workflow level, then each job of the workflow will be run on its own devices sequentially or in parallel, depending on the value of the "multiprocessing" property of the service job. If the job fails for at least one device, it is considered to have failed and the workflow will stop.
However, if you select devices at workflow level, the workflow will run for each device independently of the others (the workflow may succeed for one device, and stop at the very first task for another device due to failure).

In other words:
  - Service Instance tasks (and Sub-workflow tasks) that exist inside of a workflow will run in sequential order as defined in the workflow builder.
  - If multiple inventory devices are selected within the workflow definition, these will run independently from each other (in parallel if the ``multiprocessing`` property is activated, sequentially otherwise, while following the sequential rules of the workflow.)
  - If multiple inventory devices are selected within the individual service instance definitions (but not at the workflow instance level, since that overrides any devices selected for the individual service instances), these will run in parallel if Multiprocessing is enabled at the service level, otherwise they will run sequentially (device after device), but each service instance step is required to be completed by all devices before moving to the next step in the workflow.

The status of a workflow will be updated in real-time in the Workflow Builder.

Success of a Workflow
---------------------

The behavior of the workflow is such that the workflow is considered to have an overall Success status if the END job is reached. So, the END job should only be reached by a success edge when the overall status of the workflow is considered successful. If a particular service job fails, then the workflow should just stop there (with the workflow thus having an overall Failure status), or it should call a cleanup/remediation job (after which the workflow will just stop there). In the event that a failure edge reaches END, the overall status of the workflow will be success.

Position saving
---------------

Note that ``position data`` in the Workflow Builder graph is saved to the database only when the user navigates away from the graph.
  - Upon leaving the Workflow Builder page.
  - When switching to another workflow.

All other changes to the Workflow Builder graph are saved immediately.

Automatic refresh
-----------------

A workflow displayed in the Workflow Builder page is automatically updated:
  - Every 0.7 second if the workflow is currently running
  - Every 15 seconds otherwise

This allows multiple users to work concurrently on a single Workflow in the Workflow Builder.
