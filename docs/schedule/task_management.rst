==================
Service Scheduling
==================

Services can be scheduled by creating a ``Task``, from the :guilabel:`schedule/task_management` page.
You need to:
    - Choose a name.
    - Select a job (the service or workflow that you want to execute).
    - Choose a start date.
    - (Optional) Choose a frequency and an end date. If a ``Frequency`` is defined, the job will run periodically, in which case you can also choose an ``End date`` if you want the task to automatically stop running. If you define a frequency but no ``End date``, the task will run indefinitely until you manually stop it.



From the views
--------------

Select the target devices (see the :guilabel:`Views / Bindings` section of the doc), and select ``Add new task`` in the right-click menu. The devices you selected graphically will be automatically selected in the task creation process described above (step 2).

.. image:: /_static/services/service_scheduling/from_view.png
   :alt: Schedule from view
   :align: center

Refer to the :guilabel:`views/bindings` section of the docs for more information.

Service tasks
-------------

In the :guilabel:`tasks/task_management/service` page, you can find a summary of all existing "Service" tasks.

.. image:: /_static/services/service_scheduling/service_tasks.png
   :alt: Service task management
   :align: center



Periodic tasks
**************

A task is periodic if you set a frequency when scheduling it (it will be run periodically). You can use the ``Pause`` and ``Resume`` buttons in the :guilabel:`Service tasks` to pause and resume the task as needed.
