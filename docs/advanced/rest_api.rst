========
REST API
========

In this section, the word ``instance`` refers to any object type supported by eNMS. In a request,
``<instance_type>`` can be any of the following: ``device``, ``link``, ``user``, ``service``, ``task``, ``pool``.

eNMS has a REST API that can:

.. contents::
  :local:
  :depth: 1

|

|

Run a service
#############

Services can be run using a standard end point with a payload used to define service specifics.

.. code-block:: python
  :caption: **POST** Request

  /rest/run_service

|

Service Payload Criteria
************************

- ``name`` (**mandatory**) Name of the service.
- ``devices`` (default: ``[]``) List of target devices. By default, the service will run on the devices configured from the web UI
- ``pools`` (default: ``[]``) Same as devices for pools.
- ``ip_addresses`` (default: ``[]``) Same as devices for pools.
- ``payload`` (default: ``{}``) Payload of the service.
- ``async`` (default: ``false``) JSON boolean.

  - ``false`` eNMS runs the service and responds to your request when the service is done running.
    The response will contain the result of the service, but the connection might time out
    if the service takes too much time to run.
  - ``true`` eNMS runs the service in a different thread and immediately responds with the service ID.

.. code-block:: python
  :caption: Service Payload Example

  {
    "name": "my_service_or_workflow",
    "devices": ["Washington"],
    "pools": ["Pool1", "Pool2"],
    "ip_addresses": ["127.0.0.1"],
    "async": true,
    "payload": {"aid": "1-2-3", "user_identified_key": "user_identified_value"}
  }

Note:

- If you do not provide a value for ``devices`` you will get the default devices built into the web UI, even if you
  provide a value in ``pools`` or ``ip_address``.
- For Postman use the type "raw" for entering key/value pairs into the body. Body must also be formatted as application/JSON.
- Extra form data parameters passed in the body of the POST are available to that service or workflow in
  payload["rest_data"][your_key_name1] and payload["rest_data"][your_key_name2], and they can be accessed within a Service
  Instance UI form as {{payload["rest_data"][your_key_name].

Run Service Response - Synchronous
**********************************

If the "async" argument is either **false** or omitted, then the request will block
until the service has been run to completion or manually stopped.

This is subset of the JSON response returned for a device-by-device workflow.

.. code-block:: python
  :caption: Run Service Response Example - Synchronous

  {
    "runtime": "2020-04-28 12:21:11.404910",
    "success": true,
    "summary": {
        "success": [
            "Device1_Name",
            "Device2_Name"
        ],
        "failure": []
    },
    "duration": "0:00:01",
    "trigger": "REST",
    "devices": {
       ...
    },
    "errors": []
  }

Run Service Response - Asynchronous
***********************************
If the "async" argument is true, then you will get JSON response with the **runtime**
name needed to retrieve the results.

.. code-block:: python
  :caption: Run Service Response Example - async

   {
      "errors": [],
      "runtime": "2020-04-28 12:16:45.201077"
   }


Retrieve the status / results of a top-level service
####################################################

.. code-block:: python
  :caption: GET Request

  /rest/result/<service_name>/<runtime>
  /rest/result/My%20Service/2020-04-29%2000:39:22.540921

|

- You will need to replace blank spaces ' ' in the service_name and runtime with '%20'
- The **status** property in the result will show either "Running" or "Completed"

.. code-block:: python
  :caption: Get run service result - result not ready yet (200)

  {
      "status": "Running",
      "result": "No results yet."
  }

|

The response when the result is ready will look very close to the synchronous result, above - but nested one level deeper inside the "result" property, below.

.. code-block:: python
  :caption: Get run service result - result is ready (200)

  {
      "status": "Completed",
      "result": {
          "runtime": "2020-04-28 12:47:43.492570",
          "success": true,
          "summary": {
              "success": [
                  "Device1_Name",
                  "Device2_Name"
              ],
              "failure": []
          },
          "duration": "0:00:02",
  }

Retrieve or delete an instance
##############################

Retrieve all attributes for a given instance.

.. code-block:: python
  :caption: **GET** or **DELETE** Request


  /rest/instance/<instance_type>/<instance_name>



|

Retrieve a list of instances with a simple query
################################################

Retrieve all instances that mach a simple query.

::

 # via a GET method to the following URL
 https://<IP_address>/rest/query/<instance_type>?parameter1=value1&parameter2=value2...

 Example: http://enms_url/rest/query/device
 Returns all devices

 Example: http://enms_url/rest/query/device?port=22&operating_system=eos
 Returns all devices whose port is 22 and operating system EOS


|

Retreive a list of instances with customized query
##################################################

Custom table search that allows users to define desired columns to be returned. This search also allows user to define
RegEx search to be used to find matching instances.


Custom Query Request
********************

.. code-block:: python
  :caption: **POST** Request

  /rest/search

Custom Query Payload
********************

- ``type`` - Type of object to search (device, link, ...)
- ``columns`` - List of attributes that will become keys in dictionary response
- ``maximum_return_records`` - Integer indicating the maximum number of records to return
- ``search_criteria`` - Dictionary requiring two key/value pairs to define a single search parameter

.. code-block:: python
  :caption: Example

  {
    "type": "device",
      "columns": ["name", "ip_address", "configuration", "configuration_matches"],
      "maximum_return_records": 3,
      "search_criteria": {"configuration_filter": "inclusion", "configuration": "i"}
  }

.. code-block:: python
  :caption: Example

  {
    "type": "link",
      "columns": ["name", "source_name"],
      "maximum_return_records": 3,
      "search_criteria": {"name_filter": "inclusion", "name": "i"}
  }

.. code-block:: python
  :caption: Retrieve all results for a service

  {
    "type": "result",
    "columns": ["result", "service_name", "device_name", "workflow_name"],
    "search_criteria": {
      "service_name": "Regression Workflow L: superworkflow",
      "parent_runtime": "2020-05-25 11:45:25.721338"
    }
  }

In order to retrieve a result for a specific device, it is possible to add the ``device_name`` key in the search criteria.

Note:

- Possible ``columns`` (or properties) can be found in ``setup/properties.json``.
- Special ``columns``  "matches" is derived from a RegEX match "configuration", which returns the line where a regex was found
- The example above will search for configurations using the regex of "link-".
- Note the use of configuration attribute is used twice to define a single parameter in ``search_criteria``. Additional
  pairs can be added to ``search_criteria`` to further refine the search.
- Note in the above example that the attribute used to search on is not required in ``search_criteria``.
- (attribute)_filter: options include "regex", "inclusion", "exclusion".


|

Retrieve the configuration of a device
######################################

Returns the configuration for a device that has been previously retrieved from the network and stored in the application.

.. code-block:: python
  :caption: GET Request

  /rest/configuration/<device_name>

|

Create or update an instance
############################
Used to build or modify and instance in the application.

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

|

Migrate between eNMS applications
###################################

The migration system can be triggered from the REST API:

::

 # Export: via a POST method to the following URL
 https://<IP_address>/rest/migrate/export

 # Import: via a POST method to the following URL
 https://<IP_address>/rest/migrate/import

The body must contain the name of the project, the types of instance to import/export, and an boolean parameter called
``empty_database_before_import`` that tells eNMS whether or not to empty the database before importing.

Example of body:

::

 {
  "name": "test_project",
  "import_export_types": ["user", "device", "link", "pool", "service", "workflow_edge", "task"],
  "empty_database_before_import": true
 }

You can also trigger the import/export programmatically. Here's an example with the python ``requests`` library.

::

 from requests import post
 from requests.auth import HTTPBasicAuth

 post(
     'yourIP/rest/migrate/import',
     json={
         "name": "Backup",
         "empty_database_before_import": False,
         "import_export_types": ["user", "device", "link", "pool", "service", "workflow_edge", "task"],
     },
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

For the import, you need to attach the file as part of the request (of type "form-data" and not JSON). You must also set
the two following ``key`` / ``value`` pairs.

 replace: Whether or not the existing topology must be replaced by the newly imported objects


Example of python script to import programmatically:

::

 from pathlib import Path
 from requests import post
 from requests.auth import HTTPBasicAuth

 with open(Path.cwd() / 'project_name.xls', 'rb') as f:
     post(
         'https://IP/rest/topology/import',
         json={'replace': True},
         files={'file': f},
         auth=HTTPBasicAuth('admin', 'admin')
     )

For the export, you must set the name of the exported file in the JSON payload:

::

 {
     "name": "rest"
 }

|

Ping eNMS
###########

Test that eNMS is alive.

.. code-block:: python
  :caption: GET Request

  /rest/is_alive

.. code-block:: python
  :caption: Response

  {
      "name": 153558346480170,
      "cluster_id": true,
  }


|

Administration functionality
############################

Some of the functionalities available in the administration panel can be accessed from the REST API as well:

- ``update_database_configurations_from_git``: download and update device configuration from a git repository.
- ``update_all_pools``: update all pools.
- ``get_git_content``: fetch git configuration and automation content.
