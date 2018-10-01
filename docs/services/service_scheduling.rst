==================
Service scheduling
==================

You can schedule a service :
  - From the :guilabel:`services/service_management` page
  - From the geographical (:guilabel:`views/geographical_view`) or the logical view (:guilabel:`views/logical_view`)

From the Service Management page
--------------------------------

A task can be scheduled to run at a specific time, once or periodically.

For a periodic task, set the frequency in seconds in the ``Frequency`` field.
The task will run indefinitely, until it is stopped or deleted from the task management page (:guilabel:`tasks/task_management`). Optionally, an ``End date`` can be scheduled for the service to stop running automatically.

.. image:: /_static/tasks/scheduling/scheduling2.png
   :alt: test
   :align: center

.. note:: If the ``Start date`` field is left empty, the service will run immediately.

From the views
--------------

You can ``left-click`` on a device to select it, or use ``shift + left-click`` to draw a selection rectangle and select multiple devices at once.
All selected devices are highlighted in red. A ``right-click`` will automatically unselect all devices.

.. image:: /_static/views/bindings/multiple_selection.png
   :alt: Multiple selection
   :align: center

Refer to the :guilabel:`views/bindings` section of the docs for more information.


