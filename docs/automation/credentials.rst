===========
Credentials
===========

eNMS credentials
----------------

The credentials used for eNMS hashed with bcrypt and the hash is stored in the database (test mode) or stored in the Hashicorp Vault (production mode). These credentials are used only for eNMS and nothing else.

Device credentials
------------------

The credentials of a device are a property of the device itself.
    
.. image:: /_static/automation/credentials/credentials.png
   :alt: Set secret password
   :align: center

They are encrypted and stored in the database (test mode) or stored in the Hashicorp Vault (production mode). If you are using eNMS in production, you MUST use eNMS in production mode, and have a Vault set up to handle the storage of all credentials (see the installation section of the doc).
