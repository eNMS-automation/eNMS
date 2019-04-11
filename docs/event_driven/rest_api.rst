========
ReST API
========

In this section, instance refers to any device, link, service, workflow, or task in eNMS database.

eNMS has a ReST API allowing to:

- retrieve an instance.
- delete an instance
- create an instance
- update an instance
- run a Service instance or a Workflow.
- make sure eNMS is alive.

This ReST API allows other/external automation entities to invoke eNMS functions remotely/programmatically. In this way, eNMS can be integrated into a larger automation solution.

Expected ReST API Headers:

- Accept:"application/json"
- Content-Type:"application/json"
- Authorization:"Basic <xxx>"


Run a service, or a workflow
****************************

::

 # via a POST method to the following URL
 https://<IP_address>/rest/run_job

The body must contain the follwoing:

- A key titled ``name`` which is assocated to a value indicating the job you want run.
- A key titled ``devices`` which is associated to a value list of target devices. If the ``device`` value list is empty, the job will run on the devices configured from the web UI.

The body may contain the follwoing:

- A key titled ``pools`` which is associated to a value list of the specific pools you want to run.
- A key titled ``ip_addresses`` which is associated to a value list of the IPs you want to run.
- A key titled ``payload" which contains a dictionary of the keys: values specific to the service being run.

The job can be run asynchronously or not with the ``async`` key:
  - ``async`` False, you send a request to the REST API, eNMS runs the job and it responds to your request when the job is done running. The response will contain the result of the job, but the connection might time out if the job takes too much time to run.
  - ``async`` True, you run the job, eNMS starts it in a different thread and immediately respond with the job ID, so that you can fetch the result later on.
  - Async will default to ``False`` if not in the payload.

Example of body:

::

 {
   "name": "my_service_or_workflow",
   "devices": ["Washington"],
   "pools": ["Pool1", "Pool2"],
   "ip_addresses": ["127.0.0.1"],
   "async": True,
   "payload": {"aid": "1-2-3", "user_identified_key": "user_identified_value"}
 }

Note:

- If you do not provide a value for ``devices`` you will get the defualut devices built into the web UI, even if you provide a value in ``pools`` or ``ip_address``.
- For Postman use the type "raw" for entering key/value pairs into the body. Body must also be formatted as application/JSON.
- Extra form data parameters passed in the body of the POST are available to that service or workflow in payload["rest_data"][your_key_name1] and payload["rest_data"][your_key_name2], and they can be accessed within a Service Instance UI form as {{payload["rest_data"][your_key_name].


Heartbeat
*********

::

 # Test that eNMS is still alive (used for high availability mechanisms)
 https://<IP_address>/rest/is_alive

eNMS returns either "True" or the ``name`` and ``cpu_load`` if the application is alive.


Retrieve or delete an instance
******************************

::

 # via a GET or DELETE method to the following URL
 https://<IP_address>/rest/instance/<instance_type>/<instance_name>

``<instance_type>`` can be any of the following: ``device``, ``link``, ``user``, ``service``, ``workflow``, ``task``, ``pool``.
``<instance_name>`` is to be replaced by the name of the instance.

.. image:: /_static/automation/rest/get_instance.png
   :alt: GET method to retrieve a device
   :align: center


Retrieve the current configuration for a device
***********************************************

::

 # via a GET method to thet following URL
 https://<IP_address>/rest/configuration/<device_name>

will retrieve the latest/current configuration for that device.


Create or update an instance
****************************

::

 # via a POST or PUT method to the following URL
 https://<IP_address>/rest/instance/<instance_type>


Migrations
**********

The migration system can be triggered from the ReST API:

::

 # Export: via a POST method to the following URL
 https://<IP_address>/rest/migrate/export

 # Import: via a POST method to the following URL
 https://<IP_address>/rest/migrate/import

The body must contain the name of the project, the types of instance to import/export, and an boolean parameter called ``empty_database_before_import`` that tells eNMS whether or not to empty the database before importing.

Example of body:

::

 {
  "name": "test_project",
  "import_export_types": ["User", "Device", "Link", "Pool", "Service", "WorkflowEdge", "Workflow", "Task"],
  "empty_database_before_import": true
 }

You can also trigger the import/export programmatically. Here's an example with the python ``requests`` library.

::

 from json import dumps
 from requests import post
 from requests.auth import HTTPBasicAuth

 post(
     'yourIP/rest/migrate/import',
     data=dumps({
         "name": "Backup",
         "empty_database_before_import": False,
         "import_export_types": ["User", "Device", "Link", "Pool", "Service", "WorkflowEdge", "Workflow", "Task"],
     }),
     headers={'content-type': 'application/json'},
     auth=HTTPBasicAuth('admin', 'admin')
 )

Topology Import / Export
************************

The import and export of topology can be triggered from the ReST API, with a POST request to the following URL:

::

 # Export: via a POST method to the following URL
 https://<IP_address>/rest/topology/export

 # Import: via a POST method to the following URL
 https://<IP_address>/rest/topology/import

For the import, you need to attach the file as part of the request (of type "form-data" and not JSON) and set the two following ``key`` / ``value`` pairs:
 - update_pools: Whether or not pools must be updated after the topology import to take into consideration the newly imported objects.
 - replace: Whether or not the existing topology must be erased and replaced by the newly imported objects.

Example of python script to import programmatically:

::

 from json import dumps
 from pathlib import Path
 from requests import post
 from requests.auth import HTTPBasicAuth

 with open(Path.cwd() / 'project_name.xls', 'rb') as f:
     post(
         'https://IP/rest/topology/import',
         data={'replace': True, 'update_pools': False},
         files={'file': f},
         auth=HTTPBasicAuth('admin', 'admin')
     )

For the export, you must set the name of the exported file in the JSON payload:

::

 {
     "name": "rest"
 }

Swagger / OpenAPI Interface
***************************

The eNMS ReST API is documented with Swagger / OpenAPI3.0. JSON and Yaml definitions for the interface, as well as the HTML API
document can be found in the 'swagger' directory of the eNMS project.