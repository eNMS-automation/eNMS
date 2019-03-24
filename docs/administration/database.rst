========
Database
========

Backup & Restore and Database Migration
***************************************

From the ``Admin / Advanced``, eNMS also supports backup and restore, as well as migration from one eNMS version to another, utilizing an Import and Export feature.

By providing the directory name inside (eNMS_HOME)/migrations/ and selecting which eNMS object types to export/backup, eNMS serializes the stored objects for those object types into a yaml file for each subsystem. These yaml files can then be copied into a directory (also in (eNMS_HOME)/migrations/) on a new VM instance of eNMS, and then the Import function can be used to import/restore the configuration and living data of those object types.

Please note that the exported backup files do not contain the secure credentials for each of the inventory devices in plain text, as credentials are considered to be stored in a Vault in production mode.

.. image:: /_static/administration/migrations.png
   :alt: Migrations
   :align: center

.. note:: If you are migrating data on an existing instance of eNMS, you can choose tick the option ``Empty Database before Import`` to empty the database before starting the migration.

.. note:: See additional discussion of migration in the Installation Section

Database Helpers
****************

Services and Workflow logs can take up a lot of space in the database.
From the ``Admin / Advanced`` page, you can clear all logs older than a given date.

There is also a Mass Deletion function that allows for deleting all objects of a particular type. This is particularly useful if you want to delete all devices and links from a particular instance and then export the remaining services and workflows to be re-used with another inventory. After mass deleting devices and links, export the migration files to be used in another instance. Without first deleting devices and links, importing services and workflows on another instance that have embedded devices and links will result in errors.

Miscellaneous
*************

Fetch Git Configurations and Update Devices - this feature will retrieve configurations from the git 'configurations' repository and load those into the database for each matching inventory device. This is performed automatically when eNMS starts up: the git configurations repository is quietly cloned and loaded into the database. This feature allows for manual pulling of updated configurations data.

Pause and Resume Scheduler - this feature will pause and resume all scheduler tasks currently waiting to run
