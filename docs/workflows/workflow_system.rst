===============
Workflow System
===============

A workflow is a directed graph which nodes are "jobs". A job can be a service or another workflow.

Each job in eNMS returns a boolean value:
  - ``True`` if it ran successfully.
  - ``False`` otherwise.

There are two types of edge in a workflow: ``Success`` edge and ``Failure`` edge.
The ``success edge`` indicates where to move in the graph if the source job was executed with success, while the ``failure edge`` does the same thing in case of failure.
On top of that, each workflow must have a ``Start`` job and an ``End`` job for eNMS to know which job should be executed first and when to stop running the workflow.

Workflows are created and managed from the :guilabel:`workflows/workflow_management` page. 

Workflow Management
-------------------

In the :guilabel:`workflows/workflow_management` page, click on the button ``Add a new workflow`` and fill the workflow creation form.
The new workflow will be automatically added to the table of worflows.
From the same page, workflows can be edited and deleted.

.. image:: /_static/workflows/workflow_system/workflow_management.png
   :alt: Workflow management
   :align: center

Workflow Editor
---------------

The :guilabel:`workflows/workflow_editor` is the place where jobs are organized into workflows.
It contains:
  - A drop-down list with all existing workflows to switch between workflows.
  - The workflow itself, displayed as a graph. The nodes are ``jobs`` (services or workflows) and there are two types of edge: ``Success`` edge and ``Failure`` edge. If a job runs successfully, it will "follow" the ``success`` edge, otherwise the ``failure`` edge.
  - A ``general right-click menu`` (Right-click on the background).
  - A ``job-specific right-click menu`` (Right-click on a job).

The ``general right-click menu`` contains the following entries:
  - Change Mode (create edges or move a job in the editor)
  - Add Job (let you choose a job among all existing jobs)
  - Run Workflow (starts the workflow)
  - View and compare the logs of the workflow (``Workflow Logs``, ``Compare Workflow Logs``)
  - Delete Delection (all selected objects are deleted, jobs or edges)

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
