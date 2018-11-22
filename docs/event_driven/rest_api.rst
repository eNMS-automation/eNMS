========
ReST API
========

In this section, ``object`` refers to any device, link, service, workflow, or task in eNMS database.

eNMS has a ReST API allowing to:

- retrieve an object.
- delete an object
- create an object
- update an object
- run a Service instance or a Workflow.
- make sure eNMS is alive.

This ReST API allows other/external automation entities to invoke eNMS functions remotely/programmatically. In this way, eNMS can be integrated into a larger automation solution.

Retrieve or delete an object
****************************

::

 # via a GET or DELETE call to the following URL
 http://IP_address/rest/object/<object_type>/<object_name>

``<object_type>`` can be any of the following: ``device``, ``link``, ``user``, ``service``, ``workflow``, ``task``.
``<object_name>`` is to be replaced by the name of the object.

.. image:: /_static/automation/rest/get_object.png
   :alt: GET call to retrieve a device
   :align: center

Create or update an object
**************************

::

 # via a POST or PUT call to the following URL
 http://IP_address/rest/object/object_type

Run a service, or a workflow)
*****************************

::

 # via a POST call to the following URL
 http://IP_address/rest/run_job/job_name

The payload must contain a ``devices`` key with the list of target devices.
If that list is empty, the service / workflow will run on the targets configured from the web UI.

Example of payload:

::
 
 {
   "devices": ["Washington"]
 }

Heartbeat
*********

::

 # Test that eNMS is still alive (used for high availability mechanisms)
 http://IP_address/rest/is_alive

eNMS returns ``True`` if it is still alive.

Migrations
**********

The migration system can be triggered from the ReST API:

::

 # Export: via a POST call to the following URL
 http://IP_address/rest/migrate/export

 # Import: via a POST call to the following URL
 http://IP_address/rest/migrate/import

The payload must contain the name of the project, the types of object to import/export, and an boolean parameter called ``empty_database_before_import`` that tells eNMS whether or not to empty the database before importing.

Example of payload:

::

 {
  "name": "test_project",
  "import_export_types": ["User", "Device", "Link", "Pool", "Service", "WorkflowEdge", "Workflow", "Task"],
  "empty_database_before_import": "False"
 }

Topology Import / Export
************************

The import and export of topology can be triggered from the ReST API, with a POST request to the following URL:

::

 # Export: via a POST call to the following URL
 http://IP_address/rest/topology/export

 # Import: via a POST call to the following URL
 http://IP_address/rest/topology/import

For the import, you need to attach the file as part of the request (of type "form-data" and not JSON) and configure two key/value pairs:
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
         'http://IP/rest/topology/import',
         data={'replace': True, 'update_pools': False},
         files={'file': f},
         auth=HTTPBasicAuth('admin', 'admin')
     )

For the export, you must set the name of the exported file in the JSON payload:

::

 {
     "name": "rest"
 }
