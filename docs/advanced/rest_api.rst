========
REST API
========

In this section, the word ``instance`` refers to any object type supported by eNMS. In a request,
``<instance_type>`` can be any of the following: ``device``, ``link``, ``user``, ``service``, ``task``, ``pool``.

eNMS has a REST API allowing to:

.. contents::
  :local:
  :depth: 1

Ping eNMS
---------

Test that eNMS is alive.

.. code-block:: python
  :caption: GET Request

  /rest/is_alive

.. code-block:: python
  :caption: Response

  {
      "name": 153558346480170,
      "cluster_id": true,
      "cpu_load": 6.3
  }

Run a service
-------------

Request
*******

.. code-block:: python
  :caption: **POST** Request

  /rest/run_service

Payload
*******

- ``name`` (**mandatory**) Name of the service.
- ``devices`` (default: ``[]``) List of target devices. By default, the service will run on the devices configured from the web UI
- ``pools`` (default: ``[]``) Same as devices for pools.
- ``ip_addresses`` (default: ``[]``) Same as devices for pools.
- ``payload`` (default: ``{}``) Payload of the service.
- ``async`` (default: ``False``)

  - ``False`` eNMS runs the service and responds to your request when the service is done running.
    The response will contain the result of the service, but the connection might time out
    if the service takes too much time to run.
  - ``True`` eNMS runs the service in a different thread and immediately respond with the service ID.

.. code-block:: python
  :caption: Example

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

Retrieve or delete an instance
------------------------------

.. code-block:: python
  :caption: **GET** or **DELETE** Request

  /rest/instance/<instance_type>/<instance_name>

Retrieve a list of instances with a query
-----------------------------------------

You can retrieve in one query all instances that match a given set of parameters.

::

 # via a GET method to the following URL
 https://<IP_address>/rest/query/<instance_type>?parameter1=value1&parameter2=value2...

 Example: http://enms_url/rest/query/device
 Returns all devices

 Example: http://enms_url/rest/query/device?port=22&operating_system=eos
 Returns all devices whose port is 22 and operating system EOS



Retrieve the configuration of a device
--------------------------------------

.. code-block:: python
  :caption: GET Request

  /rest/configuration/<device_name>

Create or update an instance
----------------------------

::

 # via a POST or PUT method to the following URL
 https://<IP_address>/rest/instance/<instance_type>

Example of payload to schedule a task from the REST API: this payload will create (or update if it already exists) the task ``test``.

::

 {
    "name": "test",
    "service": "netmiko_check_vrf_test",
	"is_active": true,
	"devices": ["Baltimore"],
	"start_date": "13/08/2019 10:16:50"
 }

This task schedules the service ``netmiko_check_vrf_test`` to run at ``20/06/2019 23:15:15`` on the device whose name is ``Baltimore``.

Migrations
**********

The migration system can be triggered from the REST API:

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
  "import_export_types": ["user", "device", "link", "pool", "service", "workflow_edge", "task"],
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
         "import_export_types": ["user", "device", "link", "pool", "service", "workflow_edge", "task"],
     }),
     headers={'content-type': 'application/json'},
     auth=HTTPBasicAuth('admin', 'admin')
 )

Topology Import / Export
************************

The import and export of topology can be triggered from the REST API, with a POST request to the following URL:

::

 # Export: via a POST method to the following URL
 https://<IP_address>/rest/topology/export

 # Import: via a POST method to the following URL
 https://<IP_address>/rest/topology/import

For the import, you need to attach the file as part of the request (of type "form-data" and not JSON) and set the two following ``key`` / ``value`` pairs:
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
         data={'replace': True},
         files={'file': f},
         auth=HTTPBasicAuth('admin', 'admin')
     )

For the export, you must set the name of the exported file in the JSON payload:

::

 {
     "name": "rest"
 }

Administration panel functionality
**********************************

Some of the functionalities available in the administration panel can be accessed from the REST API as well:

- ``update_database_configurations_from_git``: download and update device configuration from a git repository.
- ``update_all_pools``: update all pools.
- ``get_git_content``: fetch git configuration and automation content.
