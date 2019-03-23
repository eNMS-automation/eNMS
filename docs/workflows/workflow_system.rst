===============
Workflow System
===============

A workflow is comprised of one or more jobs that when followed from start to end will execute an activity, such as a software upgrade. These jobs are constructed into a directed graph instructing the machine which job is next. The jobs in the workflow can be either a service or another workflow. A service can range from a simple query to a more complex set of commands.

Each job in eNMS returns a boolean value:
- ``True`` if it ran successfully.
- ``False`` otherwise.

There are two types of results from a workflow job: ``Success`` edge and ``Failure`` edge. If a job is executed as designed, it returns a success edge, and the workflow continues down the path to the next job as indicated in the graph. However, if a job returns atypical or correctable output it give us the failure edge, which takes a different path if provided in the graph, or stops the workflow when no path is provided in the graph. Each workflow must have a Start job and an End job for eNMS to know which job should be executed first and when to stop running the workflow.

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
- A drop-down list containing all existing workflows. This list allows switching between workflows.
- The workflow itself is displayed as a graph. The  jobs are connected by arrows of type success edge or failure edge.
- A ``general right-click menu`` can be accessed by clicking on the background or white-space.
- A ``job-specific right-click menu`` can be accessed by right clicking on a specific job.

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

Services and Workflows have a ``Waiting time`` property: this tells eNMS how much time it should wait after the Service/Subworkflow has run before it begins the next job.
This is useful if the job you're running needs time to be processed or operated upon before another job can be started.

A job can also be configured to "retry"  if the results returned are not as designed. An example execution of a job in a workflow, in terms of waiting times and retries, is as follows:

::

  First try
  time between retries pause
  Retry 1
  time between retries pause
  Retry 2  (Successful, or only 2 Retries specified)
  Waiting time pause

Workflow devices
----------------

When you create a workflow, just like with services instances, the form will also contain multiple selection fields for you to select "target devices". There is also an option to select 'Use Workflow Targets'; if this is selected, the devices for the workflow will be used for execution.  If it is not selected, the devices selected at the individual service level will be used for execution.

``Multiprocessing`` allows for multiple devices to be operated upon simultaneously:
- If Multiprocessing is disabled at the workflow level, and ``Use Workflow Targets`` has been selected, the workflow will run on each device sequentially (device after device). Devices configured at service level are ignored.
- If Multiprocessing is enabled at the workflow level, and ``Use Workflow Targets`` has been selected, the workflow will run independently and in parallel on each of the selected devices (given that the max number of processes is not exceeded). Each device will run its own independent copy of the workflow regardless of the status of the other devices. Devices configured at service level are also ignored.
- If devices are selected at service level, and ``Use Workflow Targets`` has NOT been selected, and the service level Multiprocessing property is disabled, each service will run on its own selected devices sequentially (device after device), and note that the device list for each service may be different. In this case, the workflow level 'Multiprocessing' parameter is ignored.
- If devices are selected at service level, and ``Use Workflow Targets`` has NOT been selected, and the service level Multiprocessing property is enabled, each device for a given service will run in parallel to the other devices (all selected devices running at the same time), but the workflow will stop and wait for all devices to have finished the service job before moving on to the next service in the workflow. In this case, the workflow level 'Multiprocessing' parameter is ignored.

It is important to note that if you don't select any device at workflow level, then each job of the workflow will be run on its own devices sequentially or in parallel, depending on the value of the "multiprocessing" property of the service job. If the job fails for at least one device, it is considered to have failed and the workflow will stop.
However, if you select devices at workflow level and enable ``Use Workflow Targets``, with ``Multiprocessing`` enabled, the workflow will run for each device independently of the others (the workflow may succeed for one device, and stop at the very first task for another device due to failure).

In other words:
- Service Instance tasks (and Sub-workflow tasks) that exist inside of a workflow will run in sequential order as defined in the workflow builder.
- If multiple inventory devices are selected within the workflow definition with ``Use Workflow Targets`` enabled, these will run independently from each other (in parallel if the ``multiprocessing`` property is activated, sequentially otherwise, while following the sequential rules of the workflow.)
- If multiple inventory devices are selected within the individual service instance definitions with ``Use Workflow Targets`` disabled, these will run in parallel if Multiprocessing is enabled at the service level, otherwise they will run sequentially (device after device), but each service instance step is required to be completed by all devices before moving to the next step in the workflow.

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
