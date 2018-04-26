==========
Scheduling
==========

Scheduling a script or a workflow is done from the graphical view of the network, in two steps:
    
1. Selection of the target devices
#. Scheduling the script

Target selection
----------------

You can ``left-click`` on a device to select it, or use ``shift + left-click`` to draw a selection rectangle and select multiple devices at once.
All selected devices are highlighted in red. A ``right-click`` will automatically unselect all devices.

.. image:: /_static/views/bindings/multiple_selection.png
   :alt: Multiple selection
   :align: center

Refer to the :guilabel:`views/bindings` section of the docs for more information.

Script & Workflow selection
---------------------------

The geographical and logical views have an ``Scheduling`` button.
After the target devices have been selected, click on this button to open the scheduling panel.
Enter the name of the task, and select all the scripts and workflows to run.

.. image:: /_static/tasks/scheduling/scheduling1.png
   :alt: test
   :align: center

Scheduling
----------

A task can be scheduled to run at a specific time, once or periodically.

For a periodic task, set the frequency in seconds in the ``Frequency`` field.
The task will run indefinitely, until it is stopped or deleted from the task management page (:guilabel:`tasks/task_management`). Optionally, an ``End date`` can be scheduled for the script to stop running automatically.

.. image:: /_static/tasks/scheduling/scheduling2.png
   :alt: test
   :align: center

.. note:: If the ``Start date`` field is left empty, the script will run immediately.
