==================
Service Scheduling
==================

A step is scheduled by creating a ``Task``. It is a 3-steps process:

1. Choosing a name, a waiting time and a job

The job is the service (or workflow, as you can see in the ``Workflow`` section) that you want to execute.
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

Go to the :guilabel:`services/service_management` page and click on the ``Schedule`` button for the service you want to schedule.
The ``Job`` drop-down list in the first step of the task creation will not appear: it is automatically set to the appropriate service.

.. image:: /_static/services/service_scheduling/from_service_management.png
   :alt: test
   :align: center

From the views
--------------

Select the target devices (see the :guilabel:`Views / Bindings` section of the doc), and select ``Add new task`` in the right-click menu. The devices you selected graphically will be automatically selected in the task creation process described above (step 2).

.. image:: /_static/services/service_scheduling/step1.png.png
   :alt: Multiple selection
   :align: center

Refer to the :guilabel:`views/bindings` section of the docs for more information.

Service tasks
-------------

In the :guilabel:`tasks/task_management/service` page, you can find a summary of all existing "Service" tasks.

.. image:: /_static/services/service_scheduling/service_tasks.png.png
   :alt: Multiple selection
   :align: center

From this table, you can:

  - View the logs of the task.
  - Edit the task's properties, including the scheduling properties (dates and frequency).
  - Compare the logs of the task between any two runs, any two devices.
  - Pause & resume the task.
  - Delete the task.
