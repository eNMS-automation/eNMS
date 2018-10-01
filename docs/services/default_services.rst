================
Default services
================

Netmiko Configuration Service
----------------------------

Uses Netmiko to send a list of commands to be configured on the devices.
A **driver** must be selected among all available netmiko drivers.
The list of netmiko drivers is built upon netmiko ``CLASS_MAPPER_BASE`` in ``ssh_dispatcher.py`` (https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py#L69).

.. image:: /_static/automation/services/netmiko_configuration.png
   :alt: Netmiko Configuration service
   :align: center

Netmiko File Transfer Service
----------------------------

A file transfer service sends a file to a device, or retrieve a file from a device.
It relies on Netmiko file transfer functions.
The list of netmiko drivers is built upon netmiko ``FILE_TRANSFER_MAP`` in ``ssh_dispatcher.py`` (https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py#L141).

.. image:: /_static/automation/services/netmiko_file_transfer.png
   :alt: Netmiko File Transfer service
   :align: center

.. caution:: File-transfer services only works for IOS, IOS-XE, IOS-XR, NX-OS and Junos.

Netmiko Validation Service
-------------------------

A ``Netmiko validation`` service is used to check the state of a device, in a workflow (see the ``Workflow`` section for examples about how it is used).
The list of netmiko drivers is built upon netmiko ``CLASS_MAPPER_BASE`` in ``ssh_dispatcher.py`` (https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py#L69).

There are 3 ``command`` field and 3 ``pattern`` field. For each couple of command/pattern field, eNMS will check if the expected pattern can be found in the output of the command.
If the result is positive for all 3 couples, the service will return ``True`` (allowing the workflow to go forward, following the ``success`` edges), else it will return ``False``.
The values for a ``pattern`` field can also be a regular expression.

.. image:: /_static/automation/services/netmiko_validation.png
   :alt: Netmiko validation service
   :align: center

Napalm Configuration service
----------------------------

This type of service uses Napalm to update the configuration of a device.
The list of napalm drivers is built upon napalm ``SUPPORTED DRIVER`` (https://github.com/napalm-automation/napalm/blob/develop/napalm/_SUPPORTED_DRIVERS.py).

There are two types of operations:
  - ``load merge``: add the service configuration to the existing configuration of the target.
  - ``load replace``: replace the configuration of the target with the service configuration.

.. image:: /_static/automation/services/napalm_configuration.png
   :alt: Napalm configuration service
   :align: center

Napalm Rollback Service
-----------------------

Use Napalm to Rollback a configuration.

.. image:: /_static/automation/services/napalm_rollback.png
   :alt: Napalm Rollback service
   :align: center

Napalm getters service
----------------------

A ``Napalm Getters`` service is a list of getters which output is displayed in the logs.

.. image:: /_static/automation/services/napalm_getters.png
   :alt: Napalm Getters service
   :align: center

Ansible Playbook Service
------------------------

An ``Ansible Playbook`` service sends an ansible playbook to the devices.

.. image:: /_static/automation/services/ansible_playbook.png
   :alt: Ansible Playbook service
   :align: center

ReST Call Service
-----------------

Send a ReST call (GET, POST, PUT or DELETE) to an URL with optional payload.

.. image:: /_static/automation/services/rest_call.png
   :alt: ReST Call service
   :align: center
