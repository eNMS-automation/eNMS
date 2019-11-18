===========
Credentials
===========

Hashicorp Vault
---------------

If you are using eNMS in production, you MUST set up a Hashicorp Vault to handle the storage of all credentials.
Refer to the Installation section for notes on how to setup and configure the properties of Hashicorp Vault.

User credentials
----------------

The eNMS user credentials can be used to authenticate to eNMS, as well as to authenticate to a network device.
They are stored in the database (test mode) or in the Hashicorp Vault (production mode).

Device credentials
------------------

The credentials of a device are a property of the device itself within the inventory.
    
.. image:: /_static/administration/credentials.png
   :alt: Set password
   :align: center

They are stored in the Hashicorp Vault, or in the database if no Vault has been configured.
The credentials of a device are :

- a ``username`` and a ``password`` (authentication).
- an ``enable password`` required on some devices to enter the "enable" mode.

========
Database
========

Backup & Restore and Database Migration
***************************************

From the ``Admin / Administration`` page, eNMS also supports backup and restore, as well as migration from one eNMS version to another, utilizing an Import and Export feature.

By providing a directory name and selecting which eNMS object types to export/backup, eNMS serializes the stored objects in the directory ``(eNMS_HOME)/files/migrations/directory_name``. These yaml files can then be copied into the same directory (``(eNMS_HOME)/files/migrations/``) on a new VM instance of eNMS, and then the Import function can be used to import/restore the configuration and living data of those object types.

.. image:: /_static/administration/migrations.png
   :alt: Migrations
   :align: center

.. note:: the exported backup files do not contain the secure credentials for each of the inventory devices in plain text, as credentials are considered to be stored in a Vault in production mode.

.. note:: If you are migrating data on an existing instance of eNMS, you can choose tick the option ``Empty Database before Import`` to empty the database before starting the migration.

.. note:: See additional discussion of migration in the Installation Section

Database Helpers
****************

Services and Workflow logs can take up a lot of space in the database.
From the ``Admin / Administration`` page, you can clear all logs older than a given date.

There is also a Mass Deletion function that allows for deleting all objects of a particular type. This is particularly useful if you want to delete all devices and links from a particular instance and then export the remaining services and workflows to be re-used with another inventory. After mass deleting devices and links, export the migration files to be used in another instance. Without first deleting devices and links, importing services and workflows on another instance that have embedded devices and links can result in errors.

Miscellaneous
*************

- ``Fetch Git Configurations and Update Devices``: this feature will retrieve configurations from the git 'configurations' repository and load those into the database for each matching inventory device. This is performed automatically when eNMS starts up: the git configurations repository is quietly cloned and loaded into the database. This feature allows for manual pulling of updated configurations data.
- ``Pause and Resume Scheduler``: this feature will pause and resume all scheduler tasks currently waiting to run.
- ``Reset Service Statuses``: when a service or workflow fails, it is sometimes stuck in a "Running" mode and cannot be executed. This button will reset the status of all services and workflows.

Individual export
*****************

Services and workflows can be exported and imported individually, as a .tgz archive.
This is useful when you have multiple VMs deployed with eNMS, and you need to send a service / workflow from one VM to another.

To import a service, you need to move the archive to the ``files/services`` folder,
then go to the "Administration" page and click on the ``Import services`` button.

=========================
Role-based Access Control
=========================

TBD