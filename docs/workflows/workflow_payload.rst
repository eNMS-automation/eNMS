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

  def job(self, task, payload):
      results = {'success': True, 'result': 'nothing happened'}
      for device in task.compute_targets():
          results[device.name] = True
      return results

The dictionnary ``results`` is the payload of the task, i.e the information that will be transferred to the next tasks to run in the workflow. ``results`` MUST contain a key ``success``, to tell eNMS whether the task was considered a success or not (therefore influencing how to move forward in the workflow: either via a ``Success`` edge or a ``Failure`` edge).
  
The last argument of the ``job`` function is ``payload``: it is a dictionnary that contains the ``result`` of all tasks that have already been executed.

If we consider the aforementioned workflow, the task ``task_process_payload1`` receives the variable ``payload`` that contains the results of all other tasks in the workflow (because it is the last one to be executed).

The results of the task ``task_service_napalm_getter_get_facts`` is the following:

::

  {
      "2018-10-06 01:19:05.844289": {
          "success": true,
          "expected": "",
          "router8": {
              "success": true,
              "result": {
                  "get_facts": {
                      "uptime": 25920,
                      "vendor": "Cisco",
                      "os_version": "1841 Software (C1841-SPSERVICESK9-M), Version 12.4(8), RELEASE SOFTWARE (fc1)",
                      "serial_number": "FHK111813HZ",
                      "model": "1841",
                      "hostname": "test",
                      "fqdn": "test.pynms.fr",
                      "interface_list": [
                          "FastEthernet0/0",
                          "FastEthernet0/1",
                          "Serial0/0/0",
                          "Loopback22"
                      ]
                  }
              }
          }
      }
  }

Consequently, the ``payload`` variable received by ``task_process_payload1`` will look like this:

::

  {
      "task_service_napalm_getter_get_facts": {
          "success": true,
          "expected": "",
          "router8": {
              "success": true,
              "result": {
                  "get_facts": {
                      "uptime": 25920,
                      "vendor": "Cisco",
                      "os_version": "1841 Software (C1841-SPSERVICESK9-M), Version 12.4(8), RELEASE SOFTWARE (fc1)",
                      "serial_number": "FHK111813HZ",
                      "model": "1841",
                      "hostname": "test",
                      "fqdn": "test.pynms.fr",
                      "interface_list": [
                          "FastEthernet0/0",
                          "FastEthernet0/1",
                          "Serial0/0/0",
                          "Loopback22"
                      ]
                  }
              }
          }
      },
    "task_service_napalm_getter_get_interfaces": {...},
    "task_service_napalm_getter_get_config": {...},
    etc...
  }

If we want to use the results of the Napalm getters in the final task ``task_process_payload1``, here's what the the ``job`` function of ``task_process_payload1`` could look like:

::

  def job(self, task, payload):
      int_r8 = payload['task_service_napalm_getter_get_interfaces']['router8']
      result_int_r8 = int_r8['result']['get_interfaces']
      speed_Fa0 = result_int_r8['FastEthernet0/0']['speed']
      speed_Fa1 = result_int_r8['FastEthernet0/1']['speed']
      same_speed = speed_Fa0 == speed_Fa1
      
      facts_r8 = payload['task_service_napalm_getter_get_facts']['router8']
      result_facts_r8 = facts_r8['result']['get_facts']
      uptime_less_than_50000 = result_facts_r8['uptime'] < 50000
      return {
          'success': True,
          'result': {
              'same_speed_Fa0_Fa1': same_speed,
              'uptime_less_5000': uptime_less_than_50000
          }
      }

This ``job`` function reuses the Napalm getters of two tasks of the worflow (one of which, ``task_service_napalm_getter_get_facts``, is not a direct predecessor of ``task_process_payload1``) to create new variables and inject them in the results.
