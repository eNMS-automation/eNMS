================
Default Services
================

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

Service Parameters
------------------

Netmiko Configuration Service
*****************************

Uses Netmiko to send a list of commands to be configured on the devices.

Configuration parameters for creating this service instance:

- All Netmiko parameters (see above)
- ``Content`` Paste a configuration block of text here for applying to the target device(s).
- ``Exit config mode`` Determines whether or not to exit config mode after complete.
- ``Commit Configuration`` Calls netmiko ``commit`` function of the driver to commit the configuration.

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `content` input field of its configuration form.

Netmiko File Transfer Service
*****************************

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
***********************

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

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `command` input field of its configuration form.

Netmiko Validation Service
**************************

Uses Netmiko to send commands to a device and validates the output to determine the state of that device. See the ``Workflow`` section for examples of how it is used in a workflow.

There is a ``command`` field and a ``pattern`` field. eNMS will check if the expected pattern can be found in the output of the command. The values for a ``pattern`` field can also be a regular expression.

Configuration parameters for creating this service instance:

- All Netmiko parameters (see above)
- All Validation parameters (see above)
- ``Command`` CLI command to send to the device

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `command` input field of its configuration form.

Napalm Configuration service
****************************

Uses Napalm to configure a device.

Configuration parameters for creating this service instance:

- All Napalm parameters (see above)
- ``Action`` There are two types of operations:
    - ``Load merge``: add the service configuration to the existing configuration of the target
    - ``Load replace``: replace the configuration of the target with the service configuration
- ``Content`` Paste a configuration block of text here for applying to the target device(s)

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `content` input field of its configuration form.

Napalm Rollback Service
***********************

Use Napalm to rollback a configuration.

Configuration parameters for creating this service instance:

- All Napalm parameters (see above)

Napalm Getters service
**********************

Uses Napalm to retrieve a list of getters whose output is displayed in the logs. The output can be validated with a command / pattern mechanism like the ``Netmiko Validation Service``.

Configuration parameters for creating this service instance:

- All Validation parameters (see above)
- All Napalm parameters (see above)
- ``Getters`` Napalm getters (standard retrieval APIs) are documented here: (https://napalm.readthedocs.io/en/latest/support/index.html#getters-support-matrix)

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `content_match` input field of its configuration form.

Napalm Ping service
*******************

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
*************************

Uses Napalm to connect to the selected target devices and performs a traceroute to a designated target.

Configuration parameters for creating this service instance:

- All Napalm parameters (see above)
- ``Source IP address`` Override the source ip address of the ping packet with this provided IP
- ``Timeout`` Seconds to wait before declaring timeout
- ``ttl`` Time to Live parameter, which tells routers when to discard this packet because it has been in the network too long (too many hops)
- ``vrf`` Ping a specific virtual routing and forwarding interface

Ansible Playbook Service
************************

An ``Ansible Playbook`` service sends an ansible playbook to the devices.
The output can be validated with a command / pattern mechanism, like the ``Netmiko Validation Service``.
An option allows inventory devices to be selected, such that the Ansible Playbook is run on each device in the selection. Another option allows device properties from the inventory to be passed to the ansible playbook as a dictionary.

Configuration parameters for creating this service instance:

- All Validation parameters (see above)
- ``playbook_path`` path and filename to the Ansible Playbook. For example, if the playbooks subdirectory is located inside the eNMS project directory:  playbooks/juniper_get_facts.yml
- ``arguments`` ansible-playbook command line options, which are documented here: (https://docs.ansible.com/ansible/latest/cli/ansible-playbook.html)
- ``options`` Additional --extra-vars to be passed to the playbook using the syntax {'key1':value1, 'key2': value2}.  All inventory properties are automatically passed to the playbook using --extra-vars (if pass_device_properties is selected below). These options are appended.
- ``Pass device properties to the playbook`` Pass inventory properties using --extra-vars to the playbook if checked (along with the options dictionary provided above).

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `playbook_path` and `content_match` input fields of its configuration form.

REST Call Service
*****************

Send a REST call (GET, POST, PUT or DELETE) to a URL with optional payload.
The output can be validated with a command / pattern mechanism, like the ``Netmiko Validation Service``.

Configuration parameters for creating this service instance:

- All Validation parameters (see above)
- ``Type of call`` REST type operation to be performed: GET, POST, PUT, DELETE
- ``URL`` URL to make the REST connection to
- ``Payload`` The data to be sent in POST Or PUT operation
- ``Parameters`` Additional parameters to pass in the request. From the requests library, params can be a dictionary, list of tuples or bytes that are sent in the body of the request.
- ``Headers`` Dictionary of HTTP Header information to send with the request, such as the type of data to be passed. For example, {"accept":"application/json","content-type":"application/json"}
- ``Verify SSL Certificate`` If checked (default), the SSL certificate is verified.
- ``Timeout`` Requests library timeout, which is the Float value in seconds to wait for the server to send data before giving up
- ``Username`` Username to use for authenticating with the REST server
- ``Password`` Password to use for authenticating with the REST server

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `url` and `content_match` input fields of its configuration form.

Generic File Transfer Service
*****************************

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
************

Implements a Ping from this automation server to the selected devices from inventory using either ICMP or TCP.

Configuration parameters for creating this service instance:

- ``Protocol``: Use either ICMP or TCP packets to ping the devices
- ``Ports`` Which ports to ping (should be formatted as a list of ports separated by a comma, for example "22,23,49").
- ``count``: Number of ping packets to send
- ``Timeout`` Seconds to wait before declaring timeout
- ``ttl`` Time to Live parameter, which tells routers when to discard this packet because it has been in the network too long (too many hops)
- ``packet_size`` Size of the ping packet payload to send in bytes

UNIX Command Service
********************

Runs a UNIX command **on the server where eNMS is installed**.

Configuration parameters for creating this service instance:
- ``Command``: UNIX command to run on the server
- Validation Parameters

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `url` and `content_match` input fields of its configuration form.

Python Snippet Service
**********************

Runs any python code.

In the code, you can use the following variables / functions :
- ``log``: function to add a string to the service logs.
- ``parent``: the workflow that the python snippet service is called from.
- ``save_result``: the results of the service.

Additionally, you can use all the variables and functions described in the "Advanced / Python code" section of the docs.

Configuration parameters for creating this service instance:
- ``Source code``: source code of the python script to run.

Payload Extraction Service
**************************

Extract some data from the payload with a python query, and optionally post-process the result with a regular expression or a TextFSM template.

Configuration parameters for creating this service instance:
- ``Variable1``: name of the resulting variable in the results.
- ``Python Query1``: a python query to retrieve data from the payload.
- ``Match Type1``: choose the type of post-processing: no post-processing, regular expression, or TextFSM template.
- ``Match``: regular expression or TextFSM template, depending on the value of the "Match Type1".
- Same fields replicated twice (2,3 instead of 1): the service can extract / post-process up to 3 variables.

Payload Validation Service
**************************

Extract some data from the payload, and validate it against a string or a dictionary.

Configuration parameters for creating this service instance:
- All Validation parameters (see above)
- ``Python Query``: a python query to retrieve data from the payload.
