========
REST API
========

In this section, the word ``instance`` refers to any object type supported by eNMS. In a request,
``<instance_type>`` can be any of the following: ``device``, ``link``, ``user``, ``service``, ``task``, ``pool``, ``result``.

eNMS has a REST API that can:

.. contents::
  :local:
  :depth: 1

|

|

|

Run a service
#############

Services can be run using a standard end point with a payload used to define service specifics.

    Method: Post

    Address: <server>/rest/run_service

    Parameters: None

    Payload:

    - ``name`` Name of the service.
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

|

    - If you do not provide a value for ``devices`` you will get the default devices built into the web UI, even if you
      provide a value in ``pools`` or ``ip_address``.
    - For Postman use the type "raw" for entering key/value pairs into the body. Body must also be formatted as application/JSON.
    - Extra form data parameters passed in the body of the POST are available to that service or workflow in
      payload["rest_data"][your_key_name1] and payload["rest_data"][your_key_name2], and they can be accessed within a Service
      Instance UI form as {{payload["rest_data"][your_key_name].

`Run Service Response - Synchronous`

    If the "async" argument is either false or omitted, then the request will block
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

`Run Service Response - Asynchronous`

    If the "async" argument is true, then you will get JSON response with the runtime
    name needed to retrieve the results.

.. code-block:: python
  :caption: Run Service Response Example - async

   {
      "errors": [],
      "runtime": "2020-04-28 12:16:45.201077"
   }

|

|

Get the status or results of a service
######################################

    Method: Get

    Address: <server>/rest/result/<service_name>/<runtime>

    Parameters: None

    Payload: None

    - You will need to replace blank spaces ' ' in the service_name and runtime with '%20' for URL encoding.
    - The status property in the result will show either "Running" or "Completed"

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

|

|

Retrieve or delete an instance
##############################

Retrieve all attributes for a given instance.

    Method: Get or Delete

    Address: <server>/rest/instance/<instance_type>/<instance_name>

    Parameters: None

    Payload: None

|

|


Retrieve a list of instances with a simple query
################################################

Retrieve all devices or results that mach a simple query.

    Method: Get

    Address: <server>/rest/query/<instance_type>?<parameter1>=<value1>&<parameter2>=<value2>...

    Parameters: None

    Payload: None

::

     Example: <server>/rest/query/device
     Returns all devices

     Example: <server>/rest/query/device?port=22&operating_system=eos
     Returns all devices whose port is 22 and operating system EOS

|

|

Retrieve a list of instances with a customized search
#####################################################

This custom table serach varies from the simple query by providing control over which columns to return,
the types of matching, the sort order of returned items, and the max number of returned items. This
search operates with the same filtering available within the user interface & should provide the same options.

    Method: Post

    Address: <server>/rest/search

    Parameters: None

    Payload:

    -  ``type`` - Instance type of object to search

        *  'device', 'link', 'user', 'service', 'task', 'pool', 'result'
    -  ``columns`` - List of attributes desired or used for filtering

        *  Possible values can be found in 'setup/properties.json', but generally correspond to user interface table headers
    -  ``search_criteria`` - <Optional> Dictionary referencing a value listed in ``columns`` using two key/value pairs as search criteria

        *  1st key/value: choose a value from ``columns`` as the key, and the desired filter text as the value
        *  2nd key/value: append '_filter' to the key used in the 1st key/value along with one of the following as a value indicating the type of filter 'regex', 'inclusion', 'equality'.
        *  additional pairs of key/values can be added to further refine the search
    -  ``order`` - <Optional> Allows sorting based on one of the values provided column

        *  the expected format is ``[{"column": 0, "dir": "asc"}]``
        *  the value of ``column`` is an integer from the place in the list provided to ``columns`` above
        *  the values for ``dir`` can be either "desc" for descending or the default "asc" for ascending.
    -  ``maximum_return_records`` - <Optional> Integer indicating the maximum number of records to return

|

.. code-block:: python
  :caption: Device Example

  {
    "type": "device",
      "columns": ["name", "ip_address", "configuration", "configuration_matches"],
      "maximum_return_records": 3,
      "search_criteria": {"configuration_filter": "inclusion",
                          "configuration": "loopback"}
  }

Special ``columns``  "matches" is derived from a RegEX match "configuration", which returns the line where a regex was found

|

.. code-block:: python
  :caption: Example

  {
    "type": "link",
      "columns": ["name", "source_name"],
      "maximum_return_records": 3,
      "search_criteria": {"name_filter": "inclusion",
                          "name": "name_of_link"}
  }

|

.. code-block:: python
  :caption: Retrieve the latest result of a workflow

  {
    "type": "result",
    "columns": ["parent_runtime", "result"],
    "maximum_return_records": 1,
    "search_criteria": {"workflow_name_filter": "inclusion",
                               "workflow_name": "the_name_of_workflow"
                               },
    "order": [{"column": 0,
               "dir": "desc"}]
  }

|

|


Retrieve the configuration of a device
######################################

Returns the configuration for a device that has been previously retrieved from the network and stored in the application.

    Method: Get

    Address: <server>/rest/configuration/<device_name>

    Parameters: None

    Payload: None

|

|


Create or update an instance
############################
Used to build or modify and instance in the application.

    Method: Post or Put

    Address: <server>/rest/instance/<instance_type>

    Parameters: None

    Payload: <Needs to be written>

.. code-block:: python
  :caption: schedule a task from the REST API: this payload will create (or update if it already exists) the task ``test``.

  {
    "name": "test",
    "service": "netmiko_check_vrf_test",
    "is_active": true,
    "devices": ["Baltimore"],
    "start_date": "13/08/2019 10:16:50"
  }

|

This task schedules the service ``netmiko_check_vrf_test`` to run at ``20/06/2019 23:15:15`` on the device whose name is ``Baltimore``.

|

|


Migrate between eNMS applications
###################################

The migration system can be triggered from the REST API.

    Method: Post

    Address: <server>/rest/migrate/export or <server>/rest/migrate/import

    Parameters: None

    Payload: <Needs to be written>

|

The body must contain the name of the project, the types of instance to import/export, and an boolean parameter called
``empty_database_before_import`` that tells eNMS rather or not to empty the database before importing.

Example of Payload:

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

-  Topology Import / Export


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

|


Ping eNMS
###########

Test that eNMS is alive.

    Method: Get

    Address: <server>/rest/is_alive

    Parameters: None

    Payload: None

.. code-block:: python
  :caption: Response

  {
      "name": 153558346480170,
      "cluster_id": true,
  }


|

|


Administration functionality
############################

Some of the functionalities available in the administration panel can be accessed from the REST API as well:

- ``update_database_configurations_from_git``: download and update device configuration from a git repository.
- ``update_all_pools``: update all pools.
- ``get_git_content``: fetch git configuration and automation content.
