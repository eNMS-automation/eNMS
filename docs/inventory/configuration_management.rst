========================
Configuration Management
========================

eNMS can work as a network device configuration backup tool and replace Oxidized/Rancid with the following features:
  - Poll network elements and store the latest configuration in the database
  - Store any operational data that can be retrieved from the device CLI (``show version``, etc)
  - Search for any text or regular-expression in all configurations
  - Download device configuration to a local text file
  - Use the ReST API support to return a specified device’s configuration
  - Export all configurations to a remote Git repository (e.g. Gitlab) to view differences between various revisions of a configuration

Device configuration
--------------------

Configurations are retrieved by a service called ``Operational Data Backup``, which:
  - Uses Netmiko to fetch the configuration and any operational data
  - Updates the device ``Configuration`` and ``Operational Data`` properties
  - Writes the configuration to a local text file (located in eNMS/network_data)

For some devices, the configuration cannot be retrieved with only a netmiko command.
You can create your own configuration backup service(s) if need be.
Targets are defined at the service level, like any other services.

Push configurations to git
--------------------------



Search and display the configuration
------------------------------------

From the :guilabel:`Inventory / Device Management`, you can search for a specific word
in the current configuration of all devices with the ``Advanced Search`` mechanism,
column ``Current Configuration``.
eNMS will filter the list of devices based on whether the current configuration of the device
contains this word.
By clicking on the ``Configuration`` button, you can display the device configuration.

.. image:: /_static/inventory/configuration_management/display_configuration.png
   :alt: Display Configuration.
   :align: center
