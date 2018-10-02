==================
Service scheduling
==================

A step is scheduled by creating a ``Task``. It is a 3-steps process:

1. Choosing a name and a waiting time

The waiting time is only considered when the task is used in a workflow (see the ``Workflow`` section of the doc for more information). It defines how much time to wait after the task is finished (after reloading a device for example).

.. image:: /_static/services/service_scheduling/step1.png
   :alt: Scheduling: step 1
   :align: center

#. Target selection

Targets can be selected as individual device or as pool. The resulting targets of the task will be a set composed of all selected devices, along with the devices of all selected pools.

.. image:: /_static/services/service_scheduling/step2.png
   :alt: Scheduling: step 1
   :align: center

#. Date and time selection

Three options:
  - Do not run the task (you may want to create it but schedule it later, or use it as part of a workflow)
  - Run the task now
  - Schedule a date and time for the task to run later on. If a ``Frequency`` is selected, the task will run periodically, in which case you can also choose an ``End date`` if you want the task to automatically stop running. If you define a frequency but no ``End date``, the task will run indefinitely until you manually stop it.

You can schedule a service :
  - From the :guilabel:`services/service_management` page
  - From the geographical (:guilabel:`views/geographical_view`) or the logical view (:guilabel:`views/logical_view`)

From the Service Management page
--------------------------------

.. image:: /_static/tasks/scheduling/scheduling2.png
   :alt: test
   :align: center

From the views
--------------

You can ``left-click`` on a device to select it, or use ``shift + left-click`` to draw a selection rectangle and select multiple devices at once. All selected devices are highlighted in red. A ``left-click`` on the background will automatically unselect all devices (see the :guilabel:`Views / Bindings` section of the doc).

.. image:: /_static/views/bindings/multiple_selection.png
   :alt: Multiple selection
   :align: center

Refer to the :guilabel:`views/bindings` section of the docs for more information.

Task overview
-------------

In the :guilabel:`tasks/task_management` page, you can find a summary of all existing tasks.

.. image:: /_static/tasks/management/task_table.png
   :alt: Task table
   :align: center

From this table, you can:

- view the logs of the task.
- edit the task's properties, including the scheduling properties (dates and frequency).
- delete the task.


