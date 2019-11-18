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
  - Writes the configuration to a local text file (located in eNMS/files/git/data)

For some devices, the configuration cannot be retrieved with only a netmiko command. You can create your own configuration backup service(s) if need be. Targets are defined at the service level, like any other services.
A service intended to retrieve configurations must have a special ``configuration_backup_service`` set to True.
The service ``poller_service`` runs all services whose ``configuration_backup_service`` parameter is set to ``True``, as shown in the default configuration backup service `here <https://github.com/afourmy/eNMS/blob/master/eNMS/services/configuration_management/netmiko_backup_service.py#L26>`_

Configure polling
-----------------

The polling process is controlled by the ``Poller`` task. The ``Poller`` task is configured to run the ``Configuration Management Workflow``.

.. image:: /_static/inventory/configuration_management/configuration_management_workflow.png
   :alt: Configuration Management Workflow.
   :align: center

To configure the polling mechanism to run periodically, you need to go to the :guilabel:`Scheduling / Task Management` page and start the ``Poller`` task by pressing the ``Resume`` button.
By default, the ``Poller`` task will run every hour (3600 seconds), but you can change the frequency from the ``Edit`` form.

Search and display the configuration
------------------------------------

From the :guilabel:`Inventory / Device Management` and :guilabel:`Inventory / Configuration Management` pages, you can search for a specific word in the current configuration of all devices with the ``Advanced Search`` mechanism, column ``Current Configuration``. eNMS will filter the list of devices based on whether the current configuration of the device contains this word.
By clicking on the ``Configuration`` button, you can display and compare the device configurations.

.. image:: /_static/inventory/configuration_management/display_configuration.png
   :alt: Display Configuration.
   :align: center

All runs are stored in the ``Display`` and ``Compare With`` pull-down lists:
  - Selecting a run from ``Display`` will display the associated configuration.
  - Selecting a run from ``Compare With`` will compare the configuration with the one selected in ``Display``.

Comparing two configurations will display a git-like line-by-line diff similar to the one below:

.. image:: /_static/inventory/configuration_management/compare_configurations.png
   :alt: Compare Configurations.
   :align: center
