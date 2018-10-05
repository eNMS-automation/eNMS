================
Workflow Payload
================

Task dependency
---------------

One of the property of workflows in eNMS is that a task will not start unless all of its "predecessors" tasks have been executed.

In the example below, the task ``task_process_payload1`` has two "predecessors" tasks:
  - ``task_service_napalm_getters_get_interfaces``
  - ``task_service_napalm_getters_get_config``

It will not run until ``task_service_napalm_getters_get_interfaces`` and ``task_service_napalm_getters_get_config`` have been executed.

.. image:: /_static/workflows/other_workflows/payload_transfer_workflow.png
   :alt: Payload Transfer Workflow
   :align: center

Payload transfer
----------------

The most important characteristic of workflows is the transfer of data between task. When a task starts, it is provided with the results of ALL tasks in the workflow that have already been executed (and not only the results of its "predecessors").
