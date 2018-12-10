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
  - a username and password (authentication).
  - an "enable password" required on some devices to enter the "enable" mode.
