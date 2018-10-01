=========
Workflows
=========

A workflow is a directed graph which nodes are tasks.

Each task in eNMS returns a boolean value:
- ``True`` if it ran successfully.
- ``False`` otherwise.

There are two types of edge in a workflow: ``success edge`` and ``failure edge``.
The ``success edge`` indicates where to move in the graph if the source task was executed with success, while the ``failure edge`` does the same thing in case of failure.

Workflows are created and managed from the :guilabel:`workflows/workflow_management` page. 

Creation of a workflow
**********************

In the :guilabel:`workflows/workflow_management` page, click on the button ``Add a new workflow`` and fill the workflow creation form.
The new workflow will be automatically added to the table of worflows.

.. image:: /_static/automation/workflows/workflow_creation.png
   :alt: Workflow creation
   :align: center
