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

.. note:: This Service supports variable substitution (as mentioned in the previous section) in the `content` input field of its configuration form.

Netmiko File Transfer Service
-----------------------------

Uses Netmiko to send a file to a device, or retrieve a file from a device.

A **driver** must be selected among all available netmiko file transfer drivers.The list of drivers is built upon netmiko ``FILE_TRANSFER_MAP`` in ``ssh_dispatcher.py`` (https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py#L141).

.. image:: /_static/services/default_services/netmiko_file_transfer.png
   :alt: Netmiko File Transfer service
   :align: center

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