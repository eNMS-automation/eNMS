===========
Credentials
===========

Login & username
----------------

The login and username used to connect to a device are the ones you use for eNMS.
If you create an eNMS account with login ``cisco`` and password ``cisco``, eNMS will use the same credentials to try and connect to the devices upon running a script.

Secret password
---------------

Unlike the username and password, the secret password is a property of the device itself.
The secret password is set when the node is created (whether manually or from excel import):
    
.. image:: /_static/automation/credentials/secret_password.png
   :alt: Set secret password
   :align: center
