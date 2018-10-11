================
Default Services
================

The following services are present by default in eNMS.
They can be used as models to create more complex services, or used as such if they meet your needs.

Netmiko Configuration Service
-----------------------------

Uses Netmiko to send a list of commands to be configured on the devices.

A **driver** must be selected among all available netmiko drivers. The list of drivers is built upon netmiko ``CLASS_MAPPER_BASE`` in ``ssh_dispatcher.py`` (https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py#L69).

.. image:: /_static/services/default_services/netmiko_configuration.png
   :alt: Netmiko Configuration service
   :align: center

Netmiko File Transfer Service
-----------------------------

Uses Netmiko to send a file to a device, or retrieve a file from a device.

A **driver** must be selected among all available netmiko file transfer drivers.The list of drivers is built upon netmiko ``FILE_TRANSFER_MAP`` in ``ssh_dispatcher.py`` (https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py#L141).

.. image:: /_static/services/default_services/netmiko_file_transfer.png
   :alt: Netmiko File Transfer service
   :align: center

Netmiko Validation Service
--------------------------

Uses Netmiko to validate the state of a device, in a workflow (see the ``Workflow`` section for examples about how it is used).
The list of drivers is built upon netmiko ``CLASS_MAPPER_BASE`` in ``ssh_dispatcher.py`` (https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py#L69).

There are 3 ``command`` field and 3 ``pattern`` field. For each couple of command / pattern fields, eNMS will check if the expected pattern can be found in the output of the command.

If the result is positive for all 3 couples, the service is considered successful (allowing the workflow to go forward, following the ``success`` edges), otherwise it is considered to have failed.

The values for a ``pattern`` field can also be a regular expression.

.. image:: /_static/services/default_services/netmiko_validation.png
   :alt: Netmiko validation service
   :align: center

Napalm Configuration service
----------------------------

Uses Napalm to configure a device.
The list of drivers is built upon napalm ``SUPPORTED DRIVER`` (https://github.com/napalm-automation/napalm/blob/develop/napalm/_SUPPORTED_DRIVERS.py).

There are two types of operations:
  - ``load merge``: add the service configuration to the existing configuration of the target.
  - ``load replace``: replace the configuration of the target with the service configuration.

.. image:: /_static/services/default_services/napalm_configuration.png
   :alt: Napalm configuration service
   :align: center

Napalm Rollback Service
-----------------------

Use Napalm to rollback a configuration.

.. image:: /_static/services/default_services/napalm_rollback.png
   :alt: Napalm Rollback service
   :align: center

Napalm getters service
----------------------

Uses Napalm to retrieve a list of getters which output is displayed in the logs.
The output can be validated with a command / pattern mechanism, like the ``Netmiko Validation Service``.

.. image:: /_static/services/default_services/napalm_getters.png
   :alt: Napalm Getters service
   :align: center

Ansible Playbook Service
------------------------

An ``Ansible Playbook`` service sends an ansible playbook to the devices.
The output can be validated with a command / pattern mechanism, like the ``Netmiko Validation Service``.

.. image:: /_static/services/default_services/ansible_playbook.png
   :alt: Ansible Playbook service
   :align: center

ReST Call Service
-----------------

Send a ReST call (GET, POST, PUT or DELETE) to an URL with optional payload.
The output can be validated with a command / pattern mechanism, like the ``Netmiko Validation Service``.

.. image:: /_static/services/default_services/rest_call.png
   :alt: ReST Call service
   :align: center

Update Device Service
---------------------

Update the properties of one or several devices in eNMS inventory.
This service takes a dictionnary as input: all key/value pairs of that dictionnary are used to update properties in the inventory.
Example: if you create a workflow to perform the upgrade of a device, you might want to change the value of the ``operating_system`` property in eNMS to keep the inventory up-to-date.

.. image:: /_static/services/default_services/update_device.png
   :alt: Update Device service
   :align: center
