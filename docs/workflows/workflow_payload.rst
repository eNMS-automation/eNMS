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

The code for a task ``job`` function is the following:

::

  def job(self, task, incoming_payload):
      results = {'success': True, 'result': 'nothing happened'}
      for device in task.compute_targets():
          results[device.name] = True
      return results

The dictionnary ``results`` is the payload of the task, i.e the information that will be transferred to the next tasks to run in the workflow. ``results`` MUST contain a key ``success``, to tell eNMS whether the task was considered a success or not (therefore influencing how to move forward in the workflow: either via a ``Success`` edge or a ``Failure`` edge).


  - 
  - ``results``: the task results: this 
  
The last argument of the ``job`` function is ``incoming_payload``: it is a dictionnary that contains the ``result`` of all tasks that have already been executed.


