========================
Configuration Management
========================

eNMS can work as a network device configuration backup tool, and replace Oxidized/Rancid.
  - Poll network elements and download configuration when it changes
  - Ability to easily view current configuration of a device in the inventory
  - Search feature for any text in any configuration
  - For a given inventory device, view differences between different versions of configurations (perhaps this would rely on the proposed git archival service for git diff?)
  - Download configuration for a device to a local text file
  - Use the ReST API support to return a specified device's configuration
  - Export all device configurations to a remote Git repository (e.g Gitlab)

Device configuration
--------------------

All devices are listed in the :guilabel:`inventory/configuration_management` page. Configurations are retrieved with netmiko with a command defined by the user in the column ``Command to display the configuration``.
You can edit the value of this column:
  - by clicking on the ``Parameters`` button in the table.
  - by importing a spreadsheet with a column ``configuration_command`` for each device (see the documentation on importing a network with an Excel spreadsheet).

.. image:: /_static/inventory/configuration_management/device_configuration.png
   :alt: Configuration Management table.
   :align: center

Configure the poller
--------------------

Once all commands have been set, you can activate the polling process by cliking on the ``Configure and Start Poller`` button.
The following form will pop up:

.. image:: /_static/inventory/configuration_management/poller_configuration.png.png
   :alt: Poller Configuration.
   :align: center