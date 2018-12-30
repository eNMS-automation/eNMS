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

The devices and pools property defines which devices the configuration management system will run on.
The frequency to which the poller runs is set to 3600 seconds by default.
You can also enter the address of a remote Git repository: if such a repository is configured, eNMS will push all device configurations to this repository after the polling process has completed.

.. note:: Note: For the Git push mechanism to work, you must ensure that git does not ask for credentials upon pushing to the remote Git repository. This is usually done by creating a SSH key and creating the public Git on the remote Git interface (Gitlab or Github).

Display the configuration
-------------------------

By clicking on the ``Configuration`` button, you can display and compare the device configurations.

.. image:: /_static/inventory/configuration_management/display_configuration_1.png.png
   :alt: Display Configuration.
   :align: center

All runs are stored in the ``Display`` and ``Compare With`` pull-down lists:
  - Selecting a run from ``Display`` will display the associated configuration.
  - Selecting a run from ``Compare With`` will compare the configuration with the one selected in ``Display``.

Additionnally, you can click on ``Raw logs`` to open a pop up that contains nothing but the configuration (useful for copy/pasting), and click on ``Clear`` to remove all previously stored configurations from the database.


