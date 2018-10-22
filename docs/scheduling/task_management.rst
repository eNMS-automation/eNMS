===============
Task Management
===============

Services and Workflows can be scheduled by creating a ``Task``, from the :guilabel:`schedule/task_management` page.

You need to:
    - Choose a name.
    - Select a job (the service or workflow that you want to execute).
    - Choose a start date.
    - (Optional) Choose a frequency and an end date. If a ``Frequency`` is defined, the job will run periodically, in which case you can also choose an ``End date`` if you want the task to automatically stop running. If you define a frequency but no ``End date``, the task will run indefinitely until you manually stop it.

.. image:: /_static/schedule/create_task.png
   :alt: Schedule from view
   :align: center

Task management
---------------

In the :guilabel:`schedule/task_management` page, you can find a summary of all existing tasks.

Tasks can be:
    - Edited.
    - Deleted.
    - (For periodic tasks only) Paused and resumed.

.. image:: /_static/schedule/task_management.png
   :alt: Task management
   :align: center
