========
Database
========

Backup & Restore and Migration
******************************

From the ``Admin / Database``, eNMS also supports backup and restore, as well as migration from one eNMS version to another, utilizing an Import and Export feature.

By providing the directory name inside (eNMS_HOME)/migrations/import_export/ and selecting which eNMS object types to export/backup, eNMS serializes the stored objects for those object types into a yaml file for each subsystem. These yaml files can then be copied into a directory (also in (eNMS_HOME)/migrations/import_export/) on a new VM instance of eNMS, and then the Import function can be used to import/restore the configuration and living data of those object types.

Please note that the exported backup files do not contain the secure credentials for each of the inventory devices in plain text, as credentials are considered to be stored in a Vault in production mode.

.. image:: /_static/administration/migrations.png
   :alt: Migrations
   :align: center

.. note:: If you are migrating data on an existing instance of eNMS, you can choose tick the option ``Empty Database before Import`` to empty the database before starting the migration.

Logs
****

Services and Workflows logs usually take up a lot of space in the database.
From the ``Admin / Database`` page, you can clear all logs older than a given date.
