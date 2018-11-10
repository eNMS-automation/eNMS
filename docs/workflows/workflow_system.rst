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

Workflows are created and managed from the :guilabel:`workflows/workflow_management` page. 

Workflow Management
-------------------

In the :guilabel:`workflows/workflow_management` page, click on the button ``Add a new workflow`` and fill the workflow creation form.
The new workflow will be automatically added to the table of workflows.
From the same page, workflows can be edited and deleted.

.. image:: /_static/workflows/workflow_system/workflow_management.png
   :alt: Workflow management
   :align: center

Workflow Builder
----------------

The :guilabel:`workflows/workflow_builder` is the place where services (or other workflows) are organized into workflows.
It contains:
  - A drop-down list with all existing workflows to switch between workflows.
  - The workflow itself, displayed as a graph. The nodes are ``jobs`` (services or workflows) and there are two types of edge: ``Success`` edge and ``Failure`` edge. If a job runs successfully, it will "follow" the ``success`` edge, otherwise the ``failure`` edge.
  - A ``general right-click menu`` (Right-click on the background).
  - A ``job-specific right-click menu`` (Right-click on a job).

The ``general right-click menu`` contains the following entries:
  - Change Mode (create edges or move a job in the Workflow Builder)
  - Add Job (let you choose a job among all existing jobs)
  - Run Workflow (starts the workflow)
  - View and compare the logs of the workflow (``Workflow Logs``, ``Compare Workflow Logs``)
  - Delete Selection (all selected objects are deleted, jobs or edges)

.. image:: /_static/workflows/workflow_system/workflow_background_menu.png
   :alt: Workflow management
   :align: center

From the ``job-specific right-click menu``, you can:
  - Edit a job (service or workflow)
  - View and compare the logs of the job (``Job Logs``, ``Compare Job Logs``)
  - Set a job as start or end of the workflow (``Set as start``, ``Set as end``) for eNMS to know where the workflow starts, and where it ends.

.. image:: /_static/workflows/workflow_system/workflow_job_menu.png
   :alt: Workflow management
   :align: center

Waiting time
------------

Services and Workflows have a ``Waiting time`` property: this tells eNMS how much time it should wait after the Service/Subworkflow has run.
This is useful if for example you're reloading a device: you'll need to wait some time for the device to come back to life before moving on.
Another use-case is to run a command that takes some time to be executed. For example, on Cisco devices, deleting a VRF can takes up a few minutes.

If a script is configured to "retry" in case it is not successful, eNMS will also wait "time between retries" between each try. The execution of the service in a workflow, in terms of waiting times, would be the following:

..

  First try
  "time between retries" pause
  Retry 1
  "time between retries" pause 
  Retry 2
  "Waiting time" pause

Workflow devices
----------------

When you create a workflow, just like with services instances, the form will also contain multiple selection fields for you to select "target devices". If you don’t select any device, the devices for each Service (or sub- Workflow) will be used. If you select target devices for the workflow, all devices selected at the individual Service level will be ignored, and the workflow will run on all devices.

It is important to note that if you don't select any device at workflow level, then each task of the workflow will be run in parallel on all devices. If the task fails for at least one device, it is considered to have failed and the workflow will stop.
However, if you select devices at workflow level, the workflow will run for each device independently of the others (the workflow may suceed for one device, and stop at the very first task for another).

A workflow has a property ``Multiprocessing``:
- If that property is disabled, and devices have been selected at workflow level, the workflow will run on all devices sequentially (device after device).
- If that property is activated, the workflow will run in parallel on all devices.

In other words:
- Service Instance tasks (and Subworkflow tasks) that exist inside of a workflow will run in sequential order as defined in the workflow builder.
- If multiple inventory devices are selected within the workflow definition, these will run independently from each other (in parallel if the ``multiprocessing`` property is activated, sequentially otherwise, while following the sequential rules of the workflow.
- If multiple inventory devices are selected within the individual service instance definitions (but not at the workflow instance level, since that overrides any devices selected for the individual service instances), these will run in parallel, but each service instance step is required to be completed by all devices before moving to the next step in the workflow.

The status of a workflow will be updated in real-time in the Workflow Builder.

Success of a Workflow
---------------------

The behavior of the workflow is such that the workflow is considered to have an overall Success status if the END job is reached. So, the END job should only be reached by a success edge when the overall status of the workflow is considered successful. If a particular service job fails, then the workflow should just stop there (with the workflow thus having an overall Failure status), or it should call a cleanup/remediation job (after which the workflow will just stop there).

Position saving
---------------

Note that position data in the Workflow Builder graph is saved to the database only when the user navigates away from the graph.
  - Upon leaving the Workflow Builder page.
  - When switching to another workflow.
