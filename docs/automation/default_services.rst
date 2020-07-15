================
Default Services
================

Ansible Playbook Service
-------------------------------------------------

An ``Ansible Playbook`` service sends an ansible playbook to the devices.
The output can be validated with a command / pattern mechanism, like the ``Netmiko Validation Service``.

Configuration parameters for creating this service instance:

- ``Playbook Path`` path and filename to the Ansible Playbook. The location for displaying playbooks is configurable in
  eNMS settings.
- ``Arguments`` ansible-playbook command line options, which are documented here: (https://docs.ansible.com/ansible/latest/cli/ansible-playbook.html)
- ``Pass device properties to the playbook`` Pass inventory properties using --extra-vars to the playbook if checked
  (along with the options dictionary provided below). All device properties are passed such as ``device.name`` or ``device.ip_address``
- ``options`` Additional --extra-vars to be passed to the playbook using the syntax {'key1':value1, 'key2': value2}.
  All inventory properties are automatically passed to the playbook using --extra-vars (if pass_device_properties is
  selected above). These options are appended.
- Ansible itself supports a number of standard return codes; these are returned in the results of the service and include:

  - 0 : OK or no hosts matched
  - 1 : Error
  - 2 : One or more hosts failed
  - 3 : One or more hosts were unreachable
  - 4 : Parser error
  - 5 : Bad or incomplete options
  - 99 : User interrupted execution
  - 250 : Unexpected error

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `arguments` and
   `options` input fields of its configuration form.


Netmiko Services
--------------------------------------------------

The Netmiko services provide the ability to perform multiple actions through an SSH connection. Below are the values
common to each Netmiko service and the specifics for each are in their own sections.

Common Netmiko Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``Driver`` This selects which Netmiko driver to use when connecting to the device. This is not used if ``Use Device Driver``
  is checked.
- ``Use Device Driver`` If checked, the driver assigned to the device in the inventory will be used.
- ``Enable mode`` If checked, Netmiko should enter enable\priviledged mode on the device before applying the above
  configuration block. For the Linux driver, this means root/sudo.
- ``Config mode`` If checked, Netmiko should enter config mode
- ``Fast CLI`` If checked, Netmiko will disable internal wait states and delays in order to execute the service as fast as possible.
- ``Timeout`` Netmiko internal timeout in seconds to wait for a connection or response before declaring failure.
- ``Delay factor`` Netmiko multiplier used to increase internal delays (defaults to 1). Delay factor is used in the
  send_command Netmiko method. See here for more explanation: (https://pynet.twb-tech.com/blog/automation/netmiko-what-is-done.html)
- ``Global delay factor`` Netmiko multiplier used to increase internal delays (defaults to 1). Global delay factor affects
  more delays beyond Netmiko send_command. Increase this for devices that have trouble buffering and responding quickly.

Jump on connect Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^

Jump on connect is designed to allow a second connection after connecting to the original device.

- ``Jump to remote device on connect`` If checked, the config items below will be processed for connection to the
  secondary device.
- ``Command that jumps to device`` Command to initiate secondary connection
- ``Expected username prompt`` Prompt expected when connecting secondary connection
- ``Device username`` The username to send when the expected username prompt is detected
- ``Expected password prompt`` Prompt expected when connecting secondary connection
- ``Device password`` The password to send when the expected password prompt is detected
- ``Expected prompt after login`` Prompt expected after successfully negotiating a connection
- ``Command to exit device back to original device`` Command required to exit the secondary connection


Netmiko Configuration Service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Uses Netmiko to send a list of commands to be configured on the devices.

Configuration parameters for creating this service instance:

- All Common Netmiko Parameters (see above)
- ``Content`` Paste a configuration block of text here for applying to the target device(s)
- ``Commit Configuration`` Calls netmiko ``commit`` function of the driver to commit the configuration
- ``Exit config mode`` Determines whether or not to exit config mode after complete
- ``Config Mode Command`` The command that will be used to enter config mode

- Advanced Netmiko Parameters
- ``Strip command`` Remove the echo of the command from the output (default: True)
- ``Strip prompt`` Remove the trailing router prompt from the output (default: True)

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `content` input
   field of its configuration form.

Netmiko File Transfer Service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Uses Netmiko to send a file to a device, or retrieve a file from a device. Only Cisco IOS and some Juniper devices are
supported at this time for SCP file transfer.

Configuration parameters for creating this service instance:

- All Common Netmiko Parameters (see above)
- ``Source file`` Source absolute path and filename of the file to send
- ``Destination file`` Destination file; absolute path and filename to send the file to
- ``File system`` Mounted filesystem for storage on the default. For example, disk1:
- ``Direction`` Upload or Download from the perspective of running on the device
- ``Disable_md5`` Disable checksum validation following the transfer
- ``Inline_transfer`` Cisco specific method of transferring files between internal components of the device
- ``Overwrite_file`` If checked, overwrite the file at the destination if it exists

Netmiko Data Backup Service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This service uses Netmiko to send commands to store information from devices.

Target Property and Commands
""""""""""""""""""""""""""""
- Property to update (e.g ``Configuration``)
- ``Commands`` - This is a series of twelve commands that are used to pull data from the device.
- ``Label`` This is the label the data will be given in the results

Search Response and Replace
"""""""""""""""""""""""""""""
- Used to filter out unwanted information
- ``Pattern`` The pattern to search through the retrieved data to replace
- ``Replace With`` This is what will be substituted when the ``pattern`` is found.

Netmiko Prompts Service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Similar to Netmiko Validation Service, but expects up to 3 interactive prompts for your remote command, such as 'Are you sure? Y/N'.
This service allows the user to specify the expected prompt and response to send for it.

Configuration parameters for creating this service instance:

- All Common Netmiko Parameters (see above)
- ``Command`` CLI command to send to the device
- ``Confirmation1`` Regular expression to match first expected confirmation question prompted by the device
- ``Response1`` response to first confirmation question prompted by the device
- ``Confirmation2`` Regular expression to match second expected confirmation question prompted by the device
- ``Response2`` response to second confirmation question prompted by the device
- ``Confirmation3`` Regular expression to match third expected confirmation question prompted by the device
- ``Response3`` response to third confirmation question prompted by the device

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `command` input
 field of its configuration form.

Netmiko Validation Service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Uses Netmiko to send commands to a device and validates the output to determine the state of that device. See the ``Workflow``
section for examples of how it is used in a workflow.

There is a ``command`` field and an ``expect string`` field in the Advanced Netmiko Parameters. eNMS will check if the
expected pattern can be found in the output of the command. The values for a ``pattern`` field can also be a regular expression.

Configuration parameters for creating this service instance:

- All Common Netmiko Parameters (see above)
- All Validation parameters (see above)
- ``Command`` CLI command to send to the device

Also included in Netmiko Advanced Parameters:
- ``Expect String`` This is the string that signifies the end of output.
- ``Auto Find Prompt`` Tries to detect the prompt automatically.

.. note:: ``Expect String`` and ``Auto Find Prompt`` are mutually exclusive; both cannot be enabled at the same time.
   If the user does not expect Netmiko to find the prompt automatically, the user should provide the expected prompt instead.

- ``Strip command`` Remove the echo of the command from the output (default: True).
- ``Strip prompt`` Remove the trailing router prompt from the output (default: True).
- ``Use Genie`` Use Cisco's Genie implementation to create structured data from cli commands. (Currently does not work
  with some vendors. Refer to this link to see which CLI commands are currently supported: https://developer.cisco.com/docs/genie-docs/)

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `command` input
   field of its configuration form.

Napalm Services
-------------------------------------------------

Napalm connections are SSH connections to equipment in which a pre-defined set of data is retrieved from the equipment
and presented to the user in a structured (dictionary) format.


Napalm Common Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^

- ``Driver`` Which Napalm driver to use when connecting to the device
- ``Use driver from device`` If set to True, the driver defined at device level (``napalm_driver`` property of the device)
  is used, otherwise the driver defined at service level (``driver`` property of the service) is used.
- ``Optional arguments`` Napalm supports a number of optional arguments that are documented here:
  (https://napalm.readthedocs.io/en/latest/support/index.html#optional-arguments)

Napalm Data Backup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This service uses Napalm to pull data from devices and store it for later comparison
and for historical tracking.

- All Napalm Common Parameters (See Above)
- ``Configuration Getters`` - Choose the configuration getter named 'Configuration'


Napalm Configuration service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Uses Napalm to configure a device.

Configuration parameters for creating this service instance:

- All Napalm parameters (see above)
- ``Action`` There are two types of operations:
    - ``Load merge``: add the service configuration to the existing configuration of the target
    - ``Load replace``: replace the configuration of the target with the service configuration
- ``Content`` Paste a configuration block of text here for applying to the target device(s)

.. note:: This service is supported by a limited set of products.
.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `content` input field
   of its configuration form.

Napalm Getters service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Uses Napalm to retrieve a list of getters whose output is displayed in the logs. The output can be validated with a
command / pattern mechanism like the ``Netmiko Validation Service``.

Configuration parameters for creating this service instance:

- All Validation parameters (see above)
- All Napalm parameters (see above)
- ``Getters`` Choose one or more getters to retrieve; Napalm getters (standard retrieval APIs) are documented here:
  (https://napalm.readthedocs.io/en/latest/support/index.html#getters-support-matrix)


.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `content_match` input field of its configuration form.

Napalm Ping service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Uses Napalm to connect to the selected target devices and performs a ping to a designated target. The output contains
ping round trip time statistics. Note that the iosxr driver does not support ping, but you can use the ios driver in its
place by not selecting ``Use_device_driver``.

Configuration parameters for creating this service instance:

- All Napalm parameters (see above)
- ``Count``: Number of ping packets to send
- ``Size`` Size of the ping packet payload to send in bytes
- ``Source IP address`` Override the source ip address of the ping packet with this provided IP
- ``Timeout`` Seconds to wait before declaring timeout
- ``Ttl`` Time to Live parameter, which tells routers when to discard this packet because it has been in the network too
  long (too many hops)
- ``Vrf`` Ping a specific virtual routing and forwarding interface


Napalm Rollback Service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use Napalm to rollback a configuration.

Configuration parameters for creating this service instance:

- All Napalm parameters (see above)

Napalm Traceroute service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Uses Napalm to connect to the selected target devices and performs a traceroute to a designated target.

Configuration parameters for creating this service instance:

- All Napalm parameters (see above)
- ``Source IP address`` Override the source ip address of the ping packet with this provided IP
- ``Timeout`` Seconds to wait before declaring timeout
- ``ttl`` Time to Live parameter, which tells routers when to discard this packet because it has been in the network too
  long (too many hops)
- ``vrf`` Ping a specific virtual routing and forwarding interface

REST Call Service
-------------------------------------------------

Send a REST call (GET, POST, PUT or DELETE) to a URL with optional payload.
The output can be validated with a command / pattern mechanism, like the ``Netmiko Validation Service``.

Configuration parameters for creating this service instance:

- ``Call Type`` REST type operation to be performed: GET, POST, PUT, DELETE
- ``Rest Url`` URL to make the REST connection to
- ``Payload`` The data to be sent in POST Or PUT operation
- ``Params`` Additional parameters to pass in the request. From the requests library, params can be a dictionary, list
  of tuples or bytes that are sent in the body of the request.
- ``Headers`` Dictionary of HTTP Header information to send with the request, such as the type of data to be passed. For
  example, {"accept":"application/json","content-type":"application/json"}
- ``Verify SSL Certificate`` If checked, the SSL certificate is verified. Default is to not verify the SSL certificate.
- ``Timeout`` Requests library timeout, which is the number of seconds to wait on a response before giving up
- ``Username`` Username to use for authenticating with the REST server
- ``Password`` Password to use for authenticating with the REST server

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `url` and `content_match`
   input fields of its configuration form.

Generic File Transfer Service
-------------------------------------------------

Transfer a single file to/from the eNMS server to the device using either SFTP or SCP.

Configuration parameters for creating this service instance:

- ``Direction`` Get or Put the file from/to the target device's filesystem
- ``Protocol`` Use SCP or SFTP to perform the transfer
- ``Source file`` For Get, source file is the path-plus-filename on the device to retrieve to the eNMS server. For Put,
  source file is the path-plus-filename on the eNMS server to send to the device.
- ``Destination file`` For Get, destination file is the path-plus-filename on the eNMS server to store the file to. For
  Put, destination file is the path-plus-filename on the device to store the file to.
- ``Missing Host Key Policy`` If checked, auto-add the host key policy on the ssh connection
- ``Load Known Host Keys`` If checked, load host keys on the eNMS server before attempting the connection
- ``Look For Keys`` Flag that is passed to the paramiko ssh connection to indicate if the library should look for host keys or ignore.
- ``Source file includes glob pattern (Put Direction only)`` Flag indicates that for Put Direction transfers only, the
  above Source file field contains a Glob pattern match (https://en.wikipedia.org/wiki/Glob_(programming)) for selecting
  multiple files for transport. When Globing is used, the Destination file directory should only contain a destination
  directory, because the source file names will be re-used at the destination.
- ``Max Transfer Size`` This is that maximum packet size that will be used during transfer. This may adversely impact transfer times.
- ``Window Size`` This is the requested windows size during transfer. This may adversely impact transfer times.

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `url` and `content_match`
   input fields of its configuration form.

ICMP\TCP Ping
-------------------------------------------------

Implements a Ping from this automation server to the selected devices from inventory using either ICMP or TCP.

Configuration parameters for creating this service instance:

- ``Protocol``: Use either ICMP or TCP packets to ping the devices
- ``Ports (TCP ping only)`` Which ports to ping (should be formatted as a list of ports separated by a comma, for example "22,23,49").
- ``Count``: Number of ping packets to send
- ``Timeout`` Seconds to wait before declaring timeout
- ``Ttl`` Time to Live parameter, which tells routers when to discard this packet because it has been in the network too long (too many hops)
- ``Packet Size`` Size of the ping packet payload to send in bytes

UNIX Command Service
-------------------------------------------------

Runs a UNIX command **on the server where eNMS is installed**.

Configuration parameters for creating this service instance:
- ``Command``: UNIX command to run on the server

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `url` and `content_match`
   input fields of its configuration form.

UNIX Shell Service
-------------------------------------------------

Runs a BASH script on the server where eNMS is installed.
- ``Source Code`` Bash code to be run on the server.

Mail Notification Service
-------------------------------------------------

This service is used to send an automatically generated email to a list of recipients.

- ``Title`` Subject Line of the Email
- ``Sender`` If left blank, the email address set in the ``settings.json`` will be used.
- ``Recipients`` A comma delimited list of recipients for the email
- ``Reply-to Address`` If left blank, the reply-to address from ``settings.json`` is used. If populated, this email will
  be used by anyone replying to the automated email notification.
- ``Body`` This is the body of the email.

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `url` and `content_match`
   input fields of its configuration form.

Mattermost Notification Service
-------------------------------------------------

This service will send a message to a mattermost server that is configured in the site settings.

- ``Channel`` The channel the message will be posted to
- ``Body`` The body of the message that will be posted to the above channel

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `url` and `content_match`
   input fields of its configuration form.

Python Snippet Service
-------------------------------------------------

Runs any python code.

In the code, you can use the following variables / functions :
- ``log``: function to add a string to the service logs.
- ``parent``: the workflow that the python snippet service is called from.
- ``save_result``: the results of the service.

Additionally, you can use all the variables and functions described in the "Advanced / Python code" section of the docs.

Configuration parameters for creating this service instance:
- ``Source code``: source code of the python script to run.

Payload Extraction Service
-------------------------------------------------

Extract some data from the payload with a python query, and optionally post-process the result with a regular expression or a TextFSM template.

Configuration parameters for creating this service instance:
- ``Variable Name``: name of the resulting variable in the results.
- ``Python Extraction Query``: a python query to retrieve data from the payload.
- ``Post Processing``: choose the type of post-processing: Use Value as Extracted, Apply Regular Expression(findall), or TextFSM template.
- ``Regular Expression/ TestFSM Template Text``: regular expression or TextFSM template, depending on the value of the "Match Type1".
- ``Operation`` Choose the operation type: Set/Replace, Append to a list, Extend List, Update dictionary
- Same fields replicated twice (2,3 instead of 1): the service can extract / post-process up to 3 variables.

Payload Validation Service
-------------------------------------------------

Extract some data from the payload, and validate it against a string or a dictionary.  This is used for conducting extra
validations of a prior service's result later in a workflow.

Configuration parameters for creating this service instance:

- ``Python Query``: a python query to retrieve data from the payload.

Slack Notification Service
-------------------------------------------------

This service will send a message to the slack server that is configured in the site settings.

- ``Channel`` The channel the message will be posted to
- ``Token`` API Token to allow communications to the workspace
- ``Body`` The body of the message that will be posted to the above channel

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `url` and `content_match` input fields of its configuration form.

Topology Import Service
-------------------------------------------------

Import the topology from an instance of LibreNMS, Netbox or OpenNMS.

- ``Import Type`` Choose LibreNMS, Netbox or OpenNMS

Netbox
^^^^^^^^^^^

Configuration settings and options for importing topology from a Netbox Server

- ``Netbox Address`` Address for the netbox server
- ``Netbox Token`` API token to allow netbox interactions

OpenNMS
^^^^^^^^^^^^^

Options available for importing a known set of devices from OpenNMS

- ``Opennms Adress`` Address for the OpenNMS server
- ``Opennms Devices`` A list of devices to query in the OpenNMS server
- ``Opennms Login`` Login for the OpenNMS Server
- ``Opennms Password`` Password for the OpenNMS Server

LibreNMS
^^^^^^^^^^^^^^^^^^^

Configuration settings and options for importing topology from LibreNMS
- ``Librenms Address`` Address for the LibreNMS Server
- ``Librenms Token`` API token for allowing interaction with LibreNMS.