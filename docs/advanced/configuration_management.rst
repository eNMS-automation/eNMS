========================
Configuration Management
========================

eNMS can be used as a device configuration backup tool, like Oxidized/Rancid, with the following features:
  - Poll network devices and store the latest configuration in the database
  - Store any operational data that can be retrieved from the device CLI (e.g ``show version``, ``get facts`` etc.)
  - Search for any text or regular-expression in all configurations
  - Download device configuration to a local text file
  - Use the REST API support to return a specified device’s configuration
  - Export all configurations to a remote Git repository (e.g. Gitlab)
  - View git-style differences between various revisions of a configuration

Device configuration
--------------------

Configurations are retrieved by a service called "Netmiko Data Backup", which:
  - Fetch the device configuration using Netmiko
  - Updates the device ``Configuration`` property

For some devices, the configuration cannot be retrieved with only a netmiko command. In this case, you can either use the
"Napalm Data Backup" service to substitute a napalm getter, such as get_config, in place of retrieving the configuration
via CLI command, or you can create your own configuration backup service(s) if required. Targets are defined at the service
level, like any other services.

Push configurations to git
--------------------------

Configurations are written to a local text file, located in ``/network_data/``, which is mapped in the ``settings.json``
to a git repository.  Upon retrieving the current configuration from a device, the config is added to the database, as well
to the local text file. Git is used for storing historical revisions of the data, and each additional instance of eNMS
can retrieve the Git history using the ``Admin Button -> Fetch Git Configurations Button``. Git fetch
can also be configured in the cron to periodically get triggered through the CLI to update the Configurations that were
pushed into Git by another instance of eNMS.

Search and display the configuration
------------------------------------

From the :guilabel:`Inventory -> Configurations`, you can search for a specific word, a string that is included in a
pattern or a regular expression in the current configuration of all devices, using the `Configuration` column. eNMS
will filter the list of devices based on whether the current configuration of the device contains the search criteria.
Select the "Lines of Context" slider at the top of the UI to see, up to 5 lines, before and after, the specified word
that was searched.

By clicking on the ``Network Data`` button on the right of the screen, you can display the device Configuration

.. image:: /_static/base/configuration_search.png
   :alt: Configuration Search.
   :align: center

By clicking on the ``Historic`` button on the right of the screen, you can view the differences between various
revisions of the device configuration

.. image:: /_static/base/configuration_history.png
   :alt: Configuration Comparison.
   :align: center

