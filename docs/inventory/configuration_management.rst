========================
Configuration Management
========================

eNMS can work as a network device configuration backup tool and replace Oxidized/Rancid with the following features:
  - Poll network elements download configurations when they change
  - Easily view current configuration of a device in the inventory
  - Search for any text in any configuration
  - View differences between various revisions of a configuration
  - Download device configuration to a local text file
  - Use the ReST API support to return a specified device's configuration
  - Export all device configurations to a remote Git repository (e.g. Gitlab)

Device configuration
--------------------

All devices are listed in the :guilabel:`inventory/configuration_management` page. Configurations are retrieved with netmiko with a command defined by the user in the column ``Command to display the configuration``.
You can edit the value of this column:
  - by clicking on the ``Parameters`` button in the table.
  - by importing a spreadsheet with a column ``configuration_command`` for each device (see the documentation on importing a network with an Excel spreadsheet).

.. image:: /_static/inventory/configuration_management/device_configuration.png
   :alt: Configuration Management table.
   :align: center

Configure polling
-----------------

Once all commands have been set, you can activate the polling process by clicking on the ``Configure and Start Poller`` button.
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

.. image:: /_static/inventory/configuration_management/display_configuration.png
   :alt: Display Configuration.
   :align: center

All runs are stored in the ``Display`` and ``Compare With`` pull-down lists:
  - Selecting a run from ``Display`` will display the associated configuration.
  - Selecting a run from ``Compare With`` will compare the configuration with the one selected in ``Display``.

Additionally, you can click on ``Raw logs`` to open a pop up that contains nothing but the configuration (useful for copy/pasting), and click on ``Clear`` to remove all previously stored configurations from the database.

Comparing two configurations will display a git-like line-by-line diff similar to the one below:

.. image:: /_static/inventory/configuration_management/compare_configurations.png
   :alt: Compare Configurations.
   :align: center

Search System
-------------

You can filter the list of devices in :guilabel:`inventory/configuration_management` based on the device configurations.
The filtering system uses the following parameters:
  - ``Search text``: the text (word or sentence) to search for in the configuration.
  - ``Regular expression``: whether we're looking for a regular expression match or not.
  - ``Search only current configuration`` and ``Search in all configurations``: eNMS doesn't just store the most recent configuration, but instead, it stores the 10 most recent configurations by default. You can choose whether to search for the text in the last retrieved configuration, or in all configurations stored in the database.

.. image:: /_static/inventory/configuration_management/search_configuration.png
   :alt: Search Configuration.
   :align: center

Only the devices matched by the search will be displayed in the table. You can click on the ``Undo filter`` to display all devices again.

Advanced
--------

- Number of configurations stored in the database: by default, eNMS stores the 10 most recent configurations in the database. The polling process is controlled by the ``configuration_backup`` service. You can change the number of stored configuration by changing the ``Number of configurations stored`` property.
- Configurations are retrieved with netmiko. By default, eNMS uses the driver defined at device level to run the command. You can use a driver configured at service level instead, by unticking the ``Use driver from device`` check box.
