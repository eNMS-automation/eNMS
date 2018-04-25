=======
Scripts
=======

Scripts are created from the :guilabel:`Scripts` menu. 
The following types of script are available in eNMS.

Netmiko configuration script
----------------------------

There are two types of Netmiko configuration scripts:
  - **"show" commands**: a list of “show commands” which output will be displayed in the logs.
  - **configuration**: a list of commands to be configured on the devices.

For each type, the content of the script can be:
  - ``text-based``: a list of configuration commands to be sent to the device.
  - ``template-based``: the script is a Jinja2 template. A .YAML file containing all parameters must be provided.

Finally, a **driver** must be selected among all available netmiko drivers.

.. image:: /_static/automation/scripts/netmiko_configuration_script.png
   :alt: Netmiko configuration script
   :align: center

Netmiko File transfer script
----------------------------

A file transfer script sends a file to a device, or retrieve a file from a device.
It relies on Netmiko file transfer functions.

.. image:: /_static/automation/scripts/file_transfer_script.png
   :alt: Netmiko file transfer script
   :align: center

.. caution:: File-transfer scripts only works for IOS, IOS-XE, IOS-XR, NX-OS and Junos.

Netmiko validation script
----------------------------

.. image:: /_static/automation/scripts/netmiko_validation_script.png
   :alt: Netmiko validation script
   :align: center

NAPALM configuration script
---------------------------

This type of script uses NAPALM to update the configuration of a device.

There are two types of operations:
  - ``load merge``: add the script configuration to the existing configuration of the target.
  - ``load replace``: replace the configuration of the target with the script configuration.

Just like with the ``Netmiko configuration`` script, a configuration can be either ``text-based``, or ``template-based``.

.. image:: /_static/automation/scripts/napalm_configuration_script.png
   :alt: NAPALM configuration script
   :align: center

.. note:: the NAPALM driver used by eNMS is the one you configure in the "Operating System" property of a node.
The NAPALM drivers name must be respected: ``ios, iosxr, nxos, junos, eos``.

.. note:: this script does not by itself commit the configuration. To do so, a ``NAPALM action`` script must be used (see below).

NAPALM action script
--------------------

``NAPALM action`` scripts do not have to be created: they are created by default when eNMS runs for the first time.
There are three actions:
  - ``commit``: commits the changes pushed with ``load replace`` or ``load merge``.
  - ``discard``: discards the changes before they were committed.
  - ``rollback``: rollbacks the changes after they have been committed.

NAPALM getters script
---------------------

A ``NAPALM getters`` script is a list of getters which output is displayed in the logs.

.. image:: /_static/automation/scripts/napalm_getters_script.png
   :alt: NAPALM getters script
   :align: center

.. note:: just like with the ``NAPALM configuration`` scripts, the NAPALM driver used by eNMS is the one configured in the "Operating System" property of a node.
The NAPALM drivers name must be respected: ``ios, iosxr, nxos, junos, eos``.

Ansible script
--------------

work in progress