===============
Workflow System
===============

A workflow is a directed graph which nodes are tasks.

Each task in eNMS returns a boolean value:
  - ``True`` if it ran successfully.
  - ``False`` otherwise.

There are two types of edge in a workflow: ``success edge`` and ``failure edge``.
The ``success edge`` indicates where to move in the graph if the source task was executed with success, while the ``failure edge`` does the same thing in case of failure.
On top of that, each workflow must have a ``Start`` task and an ``End`` task for eNMS to know which task should be executed first and when to stop running the workflow.

Workflows are created and managed from the :guilabel:`workflows/workflow_management` page. 

Workflow Management
-------------------

In the :guilabel:`workflows/workflow_management` page, click on the button ``Add a new workflow`` and fill the workflow creation form.
The new workflow will be automatically added to the table of worflows.
From the same page, workflows can be edited, deleted and scheduled.

.. image:: /_static/workflows/workflow_system/workflow_management.png
   :alt: Workflow management
   :align: center

.. note:: The scheduling of workflows is exactly the same as with services. Refer to the :guilabel:`Service scheduling` section of the doc for more information.

Workflow Editor
---------------

The :guilabel:`workflows/workflow_editor` is the place where tasks are organized into workflows.
It contains:
  - A drop-down list with all existing workflows to switch between workflows.
  - The workflow itself, displayed as a graph. The nodes are ``Tasks`` and there are two types of edge: ``success`` edge and ``failure edge``. If a task runs successfully, it will "follow" the ``success`` edge, otherwise the ``failure`` edge.
  - A ``general right-click menu`` (Right-click on the background).
  - A ``task-specific right-click menu`` (Right-click on a task).

The ``general right-click menu`` contains the following entries:
  - Change mode (create edges or move a task in the editor)
  - Add task (let you choose a task among all existing tasks)
  - Delete selection (all selected objects are deleted, tasks or edges)

.. image:: /_static/workflows/workflow_system/workflow_background_menu.png
   :alt: Workflow management
   :align: center

The ``task-specific right-click menu`` contains:
  - The same entries as in the ``Task Management`` webpage: ``Edit``, ``Logs``, ``Compare``
  - The ``Set as start`` and ``Set as end`` entries, for eNMS to know where the workflow starts, and where it ends.

.. image:: /_static/workflows/workflow_system/workflow_task_menu.png
   :alt: Workflow management
   :align: center
