================
Default Services
================

The following services are present by default in eNMS.
They can be used as templates to create more complex services, or used as-is if they meet your needs.

Parameters common to all services
---------------------------------

- ``General``
    - ``Name`` Service Instance names (must be unique).
    - ``Description`` Freeform description of what the service instance does
    - ``Vendor`` Label the service instance with a vendor identifier string. This is useful in sorting and searching service instances.
    - ``Operating System`` Label the service instance with an operating system identifier string. This is useful in sorting and searching service instances.
- ``Advanced``
    - ``Number of retries`` Add a number of retry attempts for targets that have reliability issues and occassionally fail. See the previous section on Retry Mechanism for more details.
    - ``Time between retries (in seconds)`` Specify a number of seconds to wait before attempting the service instance again when a failure occurs.
    - ``Send Notification`` Enable sending results notification checkbox
    - ``Send Notification Method`` Choose Mail, Mattermost, or Slack to send the results summary to. See the previous section on Service Notification for more details.
    - ``Display only failed nodes`` Include only the failed devices in the email notification body summary
    - ``Mail Recipients (separated by comma)`` Overrides the Mail Recipients specified in the Administration Panel
    - ``Waiting time (in seconds)`` How many seconds to wait after the service instance has completed running before running the next service.
- ``Targets``
    - ``Devices`` Multi-selection list of devices from the inventory
    - ``Pools`` (Filtered) pools of devices can be selected instead of, or in addition to, selecting individual devices. Multiple pools may also be selected.
    - ``Multiprocessing`` Checkbox enables parallel execution behavior when multiple devices are selected. See the document section on the Workflow System and Workflow Devices for discussion on this behavior.
    - ``Maximum Number of Processes`` Set the maximum number of device processes allowed per service instance (assumes devices selected at the service instance level)
    - ``Credentials`` Choose between device credentials from the inventory or user credentials (login credentials for the eNMS user) when connecting to each device.

Parameters common to all services that validate data
----------------------------------------------------

- ``Validation Method``: ``Text match``, ``dictionary Equality`` or ``dictionary Inclusion``. Text match means that the result is converted into a string, and eNMS can check (via ``content_match`` / ``content_match_regex``) whether there is a match or not. dictionary Equality / Inclusion means that eNMS will check the results against a dictionary specified by the user (via ``dictionary match`` property).
- ``Content Match`` expected response string to receive back (if any). Multi-line strings are supported. If no content_match is provided, the command will succeed if the connection was successfully made and command executed.
- ``Match content against Regular expression`` Enables regex parsing in the content_match field if checked; otherwise, content_match is expected to be literal string match.
- ``Dictionary Match``: dictionary against which the results must be checked (in case ``Validation Method`` is set to either ``dictionary Equality`` or ``dictionary Inclusion``.
- ``Negative Logic`` Simply reverses the pass/fail decision if checked. This is useful in the following situations:  Run a netmiko command to check active alarm status. If a specific alarm of interest is active (thus producing success on content match), negative logic will cause it to fail. Then with retries configured, keep checking the alarm status until the alarm clears (and negative logic produces a success result).
- ``Delete spaces before matching`` Removes white spaces in the result and content_match strings to increase the likelihood of getting a match. This is particularly helpful for multi-line content matches.

Parameters common to the services that use netmiko
--------------------------------------------------

- ``Privileged mode`` If checked, Netmiko should enter enable mode on the device before applying the above configuration block 
- ``Driver`` Which Netmiko driver to use when connecting to the device
- ``Use driver from device`` If set to True, the driver defined at device level (``netmiko_driver`` property of the device) is used, otherwise the driver defined at service level (``driver`` property of the service) is used. By default, this property is set to ```True`` and eNMS uses the driver defined in the ``netmiko_driver`` property of the device. A **driver** can be selected among all available netmiko drivers. The list of drivers is built upon netmiko ``CLASS_MAPPER_BASE`` in ``ssh_dispatcher.py`` (https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py#L69.
- ``Fast CLI`` If checked, Netmiko will disable internal wait states and delays in order to execute the service as fast as possible.
- ``Timeout`` Netmiko internal timeout in seconds to wait for a connection or response before declaring failure.
- ``Delay factor`` Netmiko multiplier used to increase internal delays (defaults to 1). Delay factor is used in the send_command Netmiko method. See here for more explanation: (https://pynet.twb-tech.com/blog/automation/netmiko-what-is-done.html)
- ``Global delay factor`` Netmiko multiplier used to increase internal delays (defaults to 1). Global delay factor affects more delays beyond Netmiko send_command. Increase this for devices that have trouble buffering and responding quickly.
- ``Strip command`` Remove the echo of the command from the output (default: True).
- ``Strip prompt`` Remove the trailing router prompt from the output (default: True).
- ``Auto Find Prompt``: Tries to detect the prompt automatically.

Parameters common to the services that use Napalm
-------------------------------------------------

- ``Driver`` Which Napalm driver to use when connecting to the device
- ``Use driver from device`` If set to True, the driver defined at device level (``napalm_driver`` property of the device) is used, otherwise the driver defined at service level (``driver`` property of the service) is used.
- ``Optional arguments`` Napalm supports a number of optional arguments that are documented here: (https://napalm.readthedocs.io/en/latest/support/index.html#optional-arguments)

Netmiko Configuration Service
-----------------------------

Uses Netmiko to send a list of commands to be configured on the devices.

Configuration parameters for creating this service instance:

- All Netmiko parameters (see above)
- ``Content`` Paste a configuration block of text here for applying to the target device(s).
- ``Exit config mode`` Determines whether or not to exit config mode after complete.
- ``Commit Configuration`` Calls netmiko ``commit`` function of the driver to commit the configuration.

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `content` input field of its configuration form.

Netmiko Data Extraction Service
-------------------------------

Uses Netmiko to send commands to a device and uses a regular expression for each command to capture the matching data to a user define variable name.
The user defined variables are then used in subsequent services within a workflow and can be accessed from the UI form via: ``{{payload[data extraction service instance name]["result"][variable name]}}``

Configuration parameters for creating this service instance:

- All Netmiko parameters (see above)
- ``Variable1`` User defined variable to store the regular expression matching data in the payload dictionary that is passed between services instances in a workflow
- ``Command1`` CLI command to send to the device via SSH
- ``Regular Expression1`` Regular expression match to use in filtering the response data from the command
- Same fields replicated twice (2, 3 instead of 1)

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the ``command`` input field of its configuration form.

Netmiko File Transfer Service
-----------------------------

Uses Netmiko to send a file to a device, or retrieve a file from a device.

Configuration parameters for creating this service instance:

- All Netmiko parameters (see above)
- ``Destination file`` Destination file; absolute path and filename to send the file to
- ``Direction`` Upload or Download from the perspective of running on the device
- ``disable_md5`` Disable checksum validation following the transfer
- ``File system`` Mounted filesystem for storage on the default. For example, disk1:
- ``inline_transfer`` Cisco specific method of transferring files between internal components of the device
- ``overwrite_file`` If checked, overwrite the file at the destination if it exists
- ``Source file`` Source absolute path and filename of the file to send

Netmiko Prompts Service
-----------------------

Similar to Netmiko Validation Service, but expects up to 3 interactive prompts for your remote command, such as 'Are you sure? Y/N'.
This service allows the user to specify the expected prompt and response to send for it.

Configuration parameters for creating this service instance:

- All Netmiko parameters (see above)
- All Validation parameters (see above)
- ``Command`` CLI command to send to the device
- ``confirmation1`` first expected confirmation question prompted by the device
- ``response1`` response to first confirmation question prompted by the device
- ``confirmation2`` second expected confirmation question prompted by the device
- ``response2`` response to second confirmation question prompted by the device
- ``confirmation3`` third expected confirmation question prompted by the device
- ``response3`` response to third confirmation question prompted by the device
- ``conversion_method`` Whether the response text should be considered just text, or should it try to convert to XML or JSON. Converting to JSON allows for using the Dictionary Match by providing a dictionary {"key1":"value1", "key2":"value2"} and and choosing Validation Match by dictionary equality (exact match) or inclusion (contains).

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `command` input field of its configuration form.

Netmiko Validation Service
--------------------------

Uses Netmiko to send commands to a device and validates the output to determine the state of that device. See the ``Workflow`` section for examples of how it is used in a workflow.

There is a ``command`` field and a ``pattern`` field. eNMS will check if the expected pattern can be found in the output of the command. The values for a ``pattern`` field can also be a regular expression.

Configuration parameters for creating this service instance:

- All Netmiko parameters (see above)
- All Validation parameters (see above)
- ``Command`` CLI command to send to the device
- ``conversion_method`` Whether the response text should be considered just text, or should it try to convert to XML or JSON. Converting to JSON allows for using the Dictionary Match by providing a dictionary {"key1":"value1", "key2":"value2"} and and choosing Validation Match by dictionary equality (exact match) or inclusion (contains).

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `command` input field of its configuration form.

Napalm Configuration service
----------------------------

Uses Napalm to configure a device.

Configuration parameters for creating this service instance:

- All Napalm parameters (see above)
- ``Action`` There are two types of operations:
    - ``Load merge``: add the service configuration to the existing configuration of the target
    - ``Load replace``: replace the configuration of the target with the service configuration
- ``Content`` Paste a configuration block of text here for applying to the target device(s)

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `content` input field of its configuration form.

Napalm Rollback Service
-----------------------

Use Napalm to rollback a configuration.

Configuration parameters for creating this service instance:

- All Napalm parameters (see above)

Napalm Getters service
----------------------

Uses Napalm to retrieve a list of getters whose output is displayed in the logs. The output can be validated with a command / pattern mechanism like the ``Netmiko Validation Service``.

Configuration parameters for creating this service instance:

- All Validation parameters (see above)
- All Napalm parameters (see above)
- ``Getters`` Napalm getters (standard retrieval APIs) are documented here: (https://napalm.readthedocs.io/en/latest/support/index.html#getters-support-matrix)

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `content_match` input field of its configuration form.

Napalm Ping service
-------------------

Uses Napalm to connect to the selected target devices and performs a ping to a designated target. The output contains ping round trip time statistics.
Note that the iosxr driver does not support ping, but you can use the ios driver in its place by not selecting ``use_device_driver``.

Configuration parameters for creating this service instance:

- All Napalm parameters (see above)
- ``count``: Number of ping packets to send
- ``size`` Size of the ping packet payload to send in bytes
- ``Source IP address`` Override the source ip address of the ping packet with this provided IP
- ``Timeout`` Seconds to wait before declaring timeout
- ``ttl`` Time to Live parameter, which tells routers when to discard this packet because it has been in the network too long (too many hops)
- ``vrf`` Ping a specific virtual routing and forwarding interface

Napalm Traceroute service
-------------------------

Uses Napalm to connect to the selected target devices and performs a traceroute to a designated target.

Configuration parameters for creating this service instance:

- All Napalm parameters (see above)
- ``Source IP address`` Override the source ip address of the ping packet with this provided IP
- ``Timeout`` Seconds to wait before declaring timeout
- ``ttl`` Time to Live parameter, which tells routers when to discard this packet because it has been in the network too long (too many hops)
- ``vrf`` Ping a specific virtual routing and forwarding interface

Ansible Playbook Service
------------------------

An ``Ansible Playbook`` service sends an ansible playbook to the devices.
The output can be validated with a command / pattern mechanism, like the ``Netmiko Validation Service``.
An option allows inventory devices to be selected, such that the Ansible Playbook is run on each device in the selection. Another option allows device properties from the inventory to be passed to the ansible playbook as a dictionary.

Configuration parameters for creating this service instance:

- All Validation parameters (see above)
- ``Has Device Targets`` If checked, indicates that the selected inventory devices should be passed to the playbook as its inventory using -i. Alternatively, if not checked, the ansible playbook can reference its own inventory internally using host: inventory_group and by providing an alternative inventory
- ``playbook_path`` path and filename to the Ansible Playbook. For example, if the playbooks subdirectory is located inside the eNMS project directory:  playbooks/juniper_get_facts.yml
- ``arguments`` ansible-playbook command line options, which are documented here: (https://docs.ansible.com/ansible/latest/cli/ansible-playbook.html)
- ``options`` Additional --extra-vars to be passed to the playbook using the syntax {'key1':value1, 'key2': value2}.  All inventory properties are automatically passed to the playbook using --extra-vars (if pass_device_properties is selected below). These options are appended.
- ``Pass device properties to the playbook`` Pass inventory properties using --extra-vars to the playbook if checked (along with the options dictionary provided above).

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `playbook_path` and `content_match` input fields of its configuration form.

ReST Call Service
-----------------

Send a ReST call (GET, POST, PUT or DELETE) to a URL with optional payload.
The output can be validated with a command / pattern mechanism, like the ``Netmiko Validation Service``.

Configuration parameters for creating this service instance:

- All Validation parameters (see above)
- ``Has Device Targets`` If checked, indicates that the selected inventory devices will be made available for variable substitution in the URL and payload fields. For example, URL could be: /rest/get/{{device.ip_address}}
- ``Type of call`` ReST type operation to be performed: GET, POST, PUT, DELETE
- ``URL`` URL to make the ReST connection to
- ``Payload`` The data to be sent in POST Or PUT operation
- ``Parameters`` Additional parameters to pass in the request. From the requests library, params can be a dictionary, list of tuples or bytes that are sent in the body of the request.
- ``Headers`` Dictionary of HTTP Header information to send with the request, such as the type of data to be passed. For example, {"accept":"application/json","content-type":"application/json"}
- ``Verify SSL Certificate`` If checked (default), the SSL certificate is verified.
- ``Timeout`` Requests library timeout, which is the Float value in seconds to wait for the server to send data before giving up
- ``Username`` Username to use for authenticating with the ReST server
- ``Password`` Password to use for authenticating with the ReST server

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `url` and `content_match` input fields of its configuration form.

Update Inventory Service
------------------------

Update the properties of one or several devices in eNMS inventory.
This service takes a dictionary as input: all key/value pairs of that dictionary are used to update properties in the inventory.
Example: if you create a workflow to perform the upgrade of a device, you might want to change the value of the ``operating_system`` property in eNMS to keep the inventory up-to-date.

Configuration parameters for creating this service instance:

- ``Update dictionary`` Dictionary of properties to be updated. For example, the dictionary to update the "Model" and operating_system property of all target devices: ``{"model":"ao", "operating_system":"13.4.2"}``.

Generic File Transfer Service
-----------------------------

Transfer a single file to/from the eNMS server to the device using either SFTP or SCP.

Configuration parameters for creating this service instance:

- ``Direction`` Get or Put the file from/to the target device's filesystem
- ``Protocol`` Use SCP or SFTP to perform the transfer
- ``Source file`` For Get, source file is the path-plus-filename on the device to retrieve to the eNMS server. For Put, source file is the path-plus-filename on the eNMS server to send to the device.
- ``Destination file`` For Get, destination file is the path-plus-filename on the eNMS server to store the file to. For Put, destination file is the path-plus-filename on the device to store the file to.
- ``Missing Host Key Policy`` If checked, auto-add the host key policy on the ssh connection
- ``Load known host keys`` If checked, load host keys on the eNMS server before attempting the connection
- ``Look for keys`` Flag that is passed to the paramiko ssh connection to indicate if the library should look for host keys or ignore.
- ``Source file includes glob pattern (Put Direction only)`` Flag indicates that for Put Direction transfers only, the above Source file field contains a Glob pattern match (https://en.wikipedia.org/wiki/Glob_(programming)) for selecting multiple files for transport. When Globing is used, the Destination file directory should only contain a destination directory, because the source file names will be re-used at the destination.

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `url` and `content_match` input fields of its configuration form.

Ping Service
------------

Implements a Ping from this automation server to the selected devices from inventory using either ICMP or TCP.

Configuration parameters for creating this service instance:

- ``Protocol``: Use either ICMP or TCP packets to ping the devices
- ``Ports`` Which ports to ping (should be formatted as a list of ports separated by a comma, for example "22,23,49").
- ``count``: Number of ping packets to send
- ``Timeout`` Seconds to wait before declaring timeout
- ``ttl`` Time to Live parameter, which tells routers when to discard this packet because it has been in the network too long (too many hops)
- ``packet_size`` Size of the ping packet payload to send in bytes

UNIX Command Service
--------------------

Runs a UNIX command **on the server where eNMS is installed**.

Configuration parameters for creating this service instance:
- ``Command``: UNIX command to run on the server
- Validation Parameters

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `url` and `content_match` input fields of its configuration form.

Python Snippet Service
----------------------

Runs any python code.

In the code, you can use the following variables / functions :
- ``log``: function to add a string to the service logs.
- ``parent``: the workflow that the python snippet service is called from.
- ``save_result``: the results of the service.

Additionally, you can use all the variables and functions described in the "Advanced / Python code" section of the docs.

Configuration parameters for creating this service instance:
- ``Has Device Targets`` If checked, indicates that the selected inventory devices will be made available for variable substitution in the URL and payload fields. For example, URL could be: /rest/get/{{device.ip_address}}
- ``Source code``: source code of the python script to run.

Payload Extraction Service
--------------------------

Extract some data from the payload with a python query, and optionally post-process the result with a regular expression or a TextFSM template.

Configuration parameters for creating this service instance:
- ``Has Device Targets`` If checked, indicates that the selected inventory devices will be made available for variable substitution in the URL and payload fields. For example, URL could be: /rest/get/{{device.ip_address}}
- ``Variable1``: name of the resulting variable in the results.
- ``Python Query1``: a python query to retrieve data from the payload.
- ``Match Type1``: choose the type of post-processing: no post-processing, regular expression, or TextFSM template.
- ``Match``: regular expression or TextFSM template, depending on the value of the "Match Type1".
- Same fields replicated twice (2,3 instead of 1): the service can extract / post-process up to 3 variables.

Payload Validation Service
--------------------------

Extract some data from the payload, and validate it against a string or a dictionary.

Configuration parameters for creating this service instance:
- All Validation parameters (see above)
- ``Has Device Targets`` If checked, indicates that the selected inventory devices will be made available for variable substitution in the URL and payload fields. For example, URL could be: /rest/get/{{device.ip_address}}
- ``Python Query``: a python query to retrieve data from the payload.
- ``conversion_method`` Whether the response text should be considered just text, or should it try to convert to XML or JSON. Converting to JSON allows for using the Dictionary Match by providing a dictionary {"key1":"value1", "key2":"value2"} and and choosing Validation Match by dictionary equality (exact match) or inclusion (contains).
