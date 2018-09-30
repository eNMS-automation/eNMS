===========
Credentials
===========

If you are using eNMS in production, you MUST set up a Hashicorp Vault to handle the storage of all credentials (see the installation section of the doc).

User credentials
----------------

The user credentials can be used to authenticate to eNMS, as well as to authenticate to a network device.
They are stored in the database (test mode) or in the Hashicorp Vault (production mode).

Device credentials
------------------

The credentials of a device are a property of the device itself.
    
.. image:: /_static/automation/credentials/credentials.png
   :alt: Set password
   :align: center

They are encrypted and stored in the database (test mode) or stored in the Hashicorp Vault (production mode).
The credentials of a device are :
- a username and password (authentication)
- an "enable password" required to enter the "enable" mode for some devices 
