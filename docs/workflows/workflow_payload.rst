================
Workflow Payload
================

Job dependency
--------------

If a job ``A`` must be executed before a job ``B`` in the workflow, eNMS must be made aware of that dependency by creating a  ``Prerequisite`` edge.

In the example below, the job ``process_payload1`` uses the results from ``get_facts`` and ``get_interfaces``. By creating two prerequisite edges (from ``get_facts`` to ``process_payload1`` and from ``get_interfaces`` to ``process_payload1``), we ensure that eNMS will not run ``process_payload1`` until both ``get_interfaces`` and ``get_config`` have been executed.

.. image:: /_static/workflows/payload_transfer_workflow.png
   :alt: Payload Transfer Workflow
   :align: center

Payload transfer
----------------

The most important characteristic of workflows is the transfer of data between jobs. When a job starts, it is provided with the results of ALL jobs in the workflow that have already been executed (and not only the results of its "predecessors").

The base code for a job function is the following:

::

    def job(self, payload: dict) -> dict:
        self.logs.append(f"Real-time logs displayed when the service is running.")
        # The "job" function is called when the service is executed.
        # The parameters of the service can be accessed with self (self.string1,
        # self.boolean1, etc)
        # You can look at how default services (netmiko, napalm, etc.) are
        # implemented in other folders.
        # The resulting dictionary will be displayed in the logs.
        # It must contain at least a key "success" that indicates whether
        # the execution of the service was a success or a failure.
        # In a workflow, the "success" value will determine whether to move
        # forward with a "Success" edge or a "Failure" edge.
        return {"success": True, "result": "example"}


The dictionary that is returned by ``job`` is the payload of the job, i.e the information that will be transferred to the next jobs to run in the workflow. It MUST contain a key ``success``, to tell eNMS whether the job was considered a success or not (therefore influencing how to move forward in the workflow: either via a ``Success`` edge or a ``Failure`` edge).
  
The last argument of the ``job`` function is ``payload``: it is a dictionary that contains the results of all jobs that have already been executed.

If we consider the aforementioned workflow, the job ``process_payload1`` receives the variable ``payload`` that contains the results of all other jobs in the workflow (because it is the last one to be executed).

The results of the job ``get_facts`` is the following:

::

    "get_facts": {
      "results": {
        "devices": {
          "Washington": {
            "match": "",
            "negative_logic": false,
            "result": {
              "get_facts": {
                "fqdn": "localhost",
                "hostname": "localhost",
                "interface_list": [
                  "Loopback11",
                  "Loopback15",
                  "Loopback16",
                  "Management1"
                ],
                "model": "vEOS",
                "os_version": "4.21.1.1F-10146868.42111F",
                "serial_number": "",
                "uptime": 13159,
                "vendor": "Arista"
              }
            },
            "success": true
          }
        }
      },
      "success": false
    }

Consequently, the ``payload`` variable received by ``process_payload1`` will look like this:

::

  {
    "get_facts": {
      "results": {
        "devices": {
          "Washington": {
            "match": "",
            "negative_logic": false,
            "result": {
              "get_facts": {
                "fqdn": "localhost",
                "hostname": "localhost",
                "interface_list": [
                  "Loopback11",
                  "Loopback15",
                  "Loopback16",
                  "Management1"
                ],
                "model": "vEOS",
                "os_version": "4.21.1.1F-10146868.42111F",
                "serial_number": "",
                "uptime": 13159,
                "vendor": "Arista"
              }
            },
            "success": true
          }
        }
      },
      "success": false
    }
    "get_interfaces": {...},
    "get_config": {...},
    etc...
  }

Set and get data in a workflow
------------------------------

You can define variables in the payload with the ``set_var`` function,
and retrieve data from the payload with the ``get_var`` function.
The ``set_var`` takes the following arguments:

- first argument: the name of the variable1
- the value of the variable
- an optional "section": the variable will be defined in a subdictionary of the variable dictionary.
- device: used to store device-specific variable in a dedicated section.

For example, let's consider the following python snippet:

```
set_var("global_variable", value=1050)
set_var("variable", "variable_in_variables", section="variables")
set_var("variable1", 999, device=device.name)
set_var("variable2", "1000", device=device.name, section="variables")
set_var("iteration_simple", "192.168.105.5", section="pools")
devices = ["Boston", "Cincinnati"] if device.name == "Chicago" else ["Cleveland", "Washington"]
set_var("iteration_device", devices, section="pools", device=device.name)
```

With the workflow running on two devices called "Chicago" and "Washington",
the following variables will be added to the payload:

.. image:: /_static/workflows/variable_management.png
   :alt: Variable Management
   :align: center

Use data from a previous job in the workflow
--------------------------------------------

If a job "B" needs to use the results from a previous job "A", it can access the results of job "A"
with the ``get_result`` function.
The ``get_result`` function takes two arguments:
- the name of the job (name of the service or workflow whose results you want to retrieve)
- (Optional) the name of a device, if you want to retrieve the job results for a specific device.

Example: ``get_result(job="Payload editor")``

The results of a job is always a dictionary: this is what the ``get_result`` function returns.
You can therefore treat it as a dictionary to access the content of the results:

``get_result(job="Payload editor")["runtime"]``

Use of a SwissArmyKnifeService instance to process the payload
--------------------------------------------------------------

When the only purpose of a function is to process the payload to build a "result" set or simply to determine whether the workflow is a "success" or not, the service itself does not have have any variable "parameters". It is not necessary to create a new Service (and therefore a new class, in a new file) for each of them. Instead, you can group them all in the SwissArmyKnifeService class, and add a method called after the name of the instance. The SwissArmyKnifeService class acts as a "job multiplexer" (see the ``SwissArmyKnifeService`` section of the doc).
If we want to use the results of the Napalm getters in the final job ``process_payload1``, here's what the function of ``process_payload1`` could look like:

::

    def process_payload1(self, payload: dict, device: Device) -> dict:
        # we use the name of the device to get the result for that particular
        # device.
        get_facts = payload["get_facts"]["results"]["devices"][device.name]
        get_interfaces = payload["get_interfaces"]["results"]["devices"][device.name]
        uptime_less_than_50000 = get_facts["result"]["get_facts"]["uptime"] < 50000
        mgmg1_is_up = get_interfaces["result"]["get_interfaces"]["Management1"]["is_up"]
        return {
            "success": True,
            "uptime_less_5000": uptime_less_than_50000,
            "Management1 is UP": mgmg1_is_up,
        }


This ``job`` function reuses the results of the Napalm getter ``get_facts`` (which is not a direct predecessor of ``process_payload1``) to create new variables and inject them in the results.
From the web UI, you can then create an Service Instance of ``SwissArmyKnifeService`` called ``process_payload1``, and add that instance in the workflow. When the service instance is called, eNMS will automatically use the ``process_payload1`` method, and process the payload accordingly.

.. tip:: You can run a job directly from the Workflow Builder to see if it passes (and rerun if it fails), and also which payload the job returns.
