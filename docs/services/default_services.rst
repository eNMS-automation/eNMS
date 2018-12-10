================
Default Services
================

The following services are present by default in eNMS.
They can be used as templates to create more complex services, or used as-is if they meet your needs.

Netmiko Configuration Service
-----------------------------

Uses Netmiko to send a list of commands to be configured on the devices.

A **driver** must be selected among all available netmiko drivers. The list of drivers is built upon netmiko ``CLASS_MAPPER_BASE`` in ``ssh_dispatcher.py`` (https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py#L69).

.. image:: /_static/services/default_services/netmiko_configuration.png
   :alt: Netmiko Configuration service
   :align: center

Configuration parameters for creating a service instance:
  - ``Name`` Service Instance names must be unique, as they act as a key in the result payload of a workflow
  - ``Description`` Freeform description of what the service instance does
  - ``Devices`` Multi-selection list of devices from the inventory
  - ``multiprocessing`` Checkbox enables parallel execution behavior when multiple devices are selected. See the document section on the Workflow System and Workflow Devices for discussion on this behavior.
  - ``Pools`` (Filtered) pools of devices can be selected instead of, or in addition to, selecting individual devices. Multiple pools may also be selected. 
  - ``Waiting time (in seconds)`` How many seconds to wait after the service instance has completed running before running the next job.
  - ``send_notification`` Enable sending results notification checkbox
  - ``Send Notification Method`` Choose Mail, Mattermost, or Slack to send the results summary to. See the previous section on Service Notification for more details.
  - ``Number of retries`` Add a number of retry attempts for targets that have reliability issues and occassionally fail. See the previous section on Retry Mechanism for more details.
  - ``Time between retries (in seconds)`` Specify a number of seconds to wait before attempting the service instance again when a failure occurs.
  - ``Vendor`` Label the service instance with a vendor identifier string. This is useful in sorting and searching service instances.
  - ``Operating System`` Label the service instance with an operating system identifier string. This is useful in sorting and searching service instances.
  - ``content`` Paste a configuration block of text here for applying to the target device(s)
  - ``driver`` Which Netmiko driver to use when connecting to the device
  - ``enable_mode`` If checked, Netmiko should enter enable mode on the device before applying the above configuration block
  - ``fast_cli`` If checked, Netmiko will disable internal wait states and delays in order to execute the job as fast as possible.
  - ``timeout`` Netmiko internal timeout in seconds to wait for a connection or response before declaring failure.
  - ``global_delay_factor`` Netmiko multiplier used for internal delays (defaults to 1). Increase this for devices that have trouble buffering and responding quickly.

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `content` input field of its configuration form.

Netmiko File Transfer Service
-----------------------------

Uses Netmiko to send a file to a device, or retrieve a file from a device.

A **driver** must be selected among all available netmiko file transfer drivers.The list of drivers is built upon netmiko ``FILE_TRANSFER_MAP`` in ``ssh_dispatcher.py`` (https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py#L141).

.. image:: /_static/services/default_services/netmiko_file_transfer.png
   :alt: Netmiko File Transfer service
   :align: center

Configuration parameters for creating a service instance:
  - ``Name`` Service Instance names must be unique, as they act as a key in the result payload of a workflow
  - ``Description`` Freeform description of what the service instance does
  - ``Devices`` Multi-selection list of devices from the inventory
  - ``multiprocessing`` Checkbox enables parallel execution behavior when multiple devices are selected. See the document section on the Workflow System and Workflow Devices for discussion on this behavior.
  - ``Pools`` (Filtered) pools of devices can be selected instead of, or in addition to, selecting individual devices. Multiple pools may also be selected. 
  - ``Waiting time (in seconds)`` How many seconds to wait after the service instance has completed running before running the next job.
  - ``send_notification`` Enable sending results notification checkbox
  - ``Send Notification Method`` Choose Mail, Mattermost, or Slack to send the results summary to. See the previous section on Service Notification for more details.
  - ``Number of retries`` Add a number of retry attempts for targets that have reliability issues and occassionally fail. See the previous section on Retry Mechanism for more details.
  - ``Time between retries (in seconds)`` Specify a number of seconds to wait before attempting the service instance again when a failure occurs.
  - ``Vendor`` Label the service instance with a vendor identifier string. This is useful in sorting and searching service instances.
  - ``Operating System`` Label the service instance with an operating system identifier string. This is useful in sorting and searching service instances.
  - ``dest_file`` Destination file; absolute path and filename to send the file to
  - ``direction`` Upload or Download from the perspective of running on the device
  ` ``disable_md5`` Disable checksum validation following the transfer
  - ``driver`` Which Netmiko file transfer driver to use when connecting to the device
  - ``filesystem`` Mounted filesystem for storage on the default. For example, disk1:
  - ``inline_transfer`` Cisco specific method of transferring files between internal components of the device
  - ``overwrite_file`` If checked, overwrite the file at the destination if it exists
  - ``source_file`` Source absolute path and filename of the file to send
  - ``fast_cli`` If checked, Netmiko will disable internal wait states and delays in order to execute the job as fast as possible.
  - ``timeout`` Netmiko internal timeout in seconds to wait for a connection or response before declaring failure.
  - ``global_delay_factor`` Netmiko multiplier used for internal delays (defaults to 1). Increase this for devices that have trouble buffering and responding quickly.
  
Netmiko Validation Service
--------------------------

Uses Netmiko to send commands to a device and validates the output to determine the state of that device. See the ``Workflow`` section for examples of how it is used in a workflow.
The list of drivers is built upon netmiko ``CLASS_MAPPER_BASE`` in ``ssh_dispatcher.py`` (https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py#L69).

There is a ``command`` field and a ``pattern`` field. eNMS will check if the expected pattern can be found in the output of the command. The values for a ``pattern`` field can also be a regular expression.

.. image:: /_static/services/default_services/netmiko_validation.png
   :alt: Netmiko validation service
   :align: center

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `command` input field of its configuration form.

Napalm Configuration service
----------------------------

Uses Napalm to configure a device.
The list of drivers is built upon napalm ``SUPPORTED DRIVERS`` (https://github.com/napalm-automation/napalm/blob/develop/napalm/_SUPPORTED_DRIVERS.py).

There are two types of operations:
  - ``load merge``: add the service configuration to the existing configuration of the target.
  - ``load replace``: replace the configuration of the target with the service configuration.

.. image:: /_static/services/default_services/napalm_configuration.png
   :alt: Napalm configuration service
   :align: center

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `content` input field of its configuration form.

Napalm Rollback Service
-----------------------

Use Napalm to rollback a configuration.

.. image:: /_static/services/default_services/napalm_rollback.png
   :alt: Napalm Rollback service
   :align: center

Napalm getters service
----------------------

Uses Napalm to retrieve a list of getters whose output is displayed in the logs. The output can be validated with a command / pattern mechanism like the ``Netmiko Validation Service``.

.. image:: /_static/services/default_services/napalm_getters.png
   :alt: Napalm Getters service
   :align: center

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `content_match` input field of its configuration form.

Ansible Playbook Service
------------------------

An ``Ansible Playbook`` service sends an ansible playbook to the devices.
The output can be validated with a command / pattern mechanism, like the ``Netmiko Validation Service``.
An option allows inventory devices to be selected, such that the Ansible Playbook is run on each device in the selection. Another option allows device properties from the inventory to be passed to the ansible playbook as a dictionary.

.. image:: /_static/services/default_services/ansible_playbook.png
   :alt: Ansible Playbook service
   :align: center

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `playbook_path` and `content_match` input fields of its configuration form.

ReST Call Service
-----------------

Send a ReST call (GET, POST, PUT or DELETE) to a URL with optional payload.
The output can be validated with a command / pattern mechanism, like the ``Netmiko Validation Service``.

.. image:: /_static/services/default_services/rest_call.png
   :alt: ReST Call service
   :align: center

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `url` and `content_match` input fields of its configuration form.

.. note:: You can use the following parameters from the requests library:
  ::
    params – (optional) Dictionary, list of tuples or bytes to send in the body of the Request.
    headers – (optional) Dictionary of HTTP Headers to send with the Request.
    timeout (float) How many seconds to wait for the server to send data before giving up

Update Inventory Service
---------------------

Update the properties of one or several devices in eNMS inventory.
This service takes a dictionnary as input: all key/value pairs of that dictionnary are used to update properties in the inventory.
Example: if you create a workflow to perform the upgrade of a device, you might want to change the value of the ``operating_system`` property in eNMS to keep the inventory up-to-date.

.. image:: /_static/services/default_services/update_inventory.png
   :alt: Update Inventory service
   :align: center

.. note:: Example of dictionnary to update the "Model" property of all target devices: ``{"model":"ao"}``.
