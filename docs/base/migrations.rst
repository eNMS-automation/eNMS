============================
Backup/Restore and Migration
============================

From the Inventory/Import & Export menu, eNMS also supports backup and restore, as well as migration from one eNMS version to another, utilizing an Import and Export feature. By providing the directory name inside (eNMS_HOME)/migrations/import_export/ and selecting which eNMS subsystems to export/backup, eNMS serializes the stored configurations for those subsystems into a yaml file for each subsystem. These yaml files can then be copied into a directory (also in (eNMS_HOME)/migrations/import_export/) on a new VM instance of eNMS, and then the Import function can be used to import/restore the configuration and living data of those subsystems. Please note that the exported backup files contain the secure credentials for each of the inventory devices in plain text. For this reason, backup files need to be securely protected, and the Export feature can only be initiated by a user with Administrator privileges in eNMS.

.. image:: /_static/objects/objects/migrations.png
   :alt: Migrations
   :align: center
