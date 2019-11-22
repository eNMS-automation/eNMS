============
Installation
============

Requirements: Unix server with python 3.6+

Run eNMS in test mode
---------------------

::

 # download the code from github:
 git clone https://github.com/afourmy/eNMS.git
 cd eNMS

 # install the requirements:
 pip install -r requirements.txt

 # set the FLASK_APP environment variable
 export FLASK_APP=app.py

 # start the application with Flask
 flask run --host=0.0.0.0

 # or with gunicorn
 gunicorn --config gunicorn.py app:app

Run eNMS in production
----------------------

To start eNMS in production mode, you must change the value of the  "config_mode" in the config.json file.
In production mode, the secret key is not automatically set to a default value in case it is missing.
Therefore, you must configure it yourself:

::

 # set the SECRET_KEY environment variable
 export SECRET_KEY=value-of-your-secret-key

All credentials should be stored in a Hashicorp Vault: the config variable ``active``
tells eNMS that a Vault has been setup and can be used.
Follow the manufacturer's instructions and options for how to setup a Hashicorp Vault.

You must tell eNMS how to connect to the Vault with
  - the ``address`` config variable
  - the ``VAULT_TOKEN`` environment variable

::

 # set the VAULT_TOKEN environment variable
 export VAULT_TOKEN=vault-token

eNMS can also unseal the Vault automatically at start time.
This mechanism is disabled by default. To activate it, you need to:
- set the ``unseal`` configuration variable to ``true``
- set the UNSEAL_VAULT_KEYx (``x`` in [1, 5]) environment variables :

::

 export UNSEAL_VAULT_KEY1=key1
 export UNSEAL_VAULT_KEY2=key2
 etc

You also have to tell eNMS the address of your database by setting the "DATABASE_URL" environment variable.

::

 # set the DATABASE_URL environment variable
 export DATABASE_URL=database-address

In case this environment variable is not set, eNMS will default to using a SQLite database.

Authentication with LDAP/Active Directory
-----------------------------------------

The following variables control how eNMS integrates with LDAP/Active Directory for user authentication:
  - ``active``: Set to ``true`` to enable LDAP authentication; otherwise ``false``
  - ``ldap_server``: LDAP Server URL (also called LDAP Provider URL):
  - ``ldap_userdn``: LDAP Distinguished Name (DN) for the user. This gets combined inside eNMS as
    "domain.ad.company.com\\username" before being sent to the server.
  - ``ldap_basedn``: LDAP base distinguished name subtree that is used when
    searching for user entries on the LDAP server. Use LDAP Data Interchange Format (LDIF)
    syntax for the entries.
  - ``ldap_admin_group``: string to match against 'memberOf' attributes of the matched user to determine if the user is allowed to log in.

eNMS first checks to see if the user exists locally inside eNMS.
If not and if LDAP/Active Directory is enabled, eNMS tries to authenticate
against LDAP/AD using the pure python ldap3 library, and if successful,
that user gets added to eNMS locally.

.. note:: Failure to match memberOf attribute output against LDAP_ADMIN_GROUP results in an 403 authentication error.
  An LDAP user MUST be a member of one of the "LDAP_ADMIN_GROUP" groups to authenticate.
.. note:: Because eNMS saves the user credentials for LDAP and TACACS+ into the Vault, if a user's credentials expire
  due to password aging, that user needs to login to eNMS in order for the updated credentials to be replaced in Vault storage.
  In the event that services are already scheduled with User Credentials, these might fail if the credentials
  are not updated in eNMS.

Configuration
-------------

The configuration is divided into:
  - private variables (passwords, tokens, keys) set as environment variables.
  - public variables defined in the ``config.json`` file.

Public configuration
********************

.. code-block:: python
  {
    "app": {
      "address": "",
      "config_mode": "debug",
      "create_examples": true,
      "documentation_url": "https://enms.readthedocs.io/en/latest/",
      # Gunicorn log level
      "log_level": "debug",

      # Git is used as a version control system for device configurations.
      "git_repository": ""
    },
    "cluster": {
      "active": false,
      "id": true,
      "scan_subnet": "192.168.105.0/24",
      "scan_protocol": "http",
      "scan_timeout": 0.05
    },
    "database": {
      "url": "sqlite:///database.db?check_same_thread=False",
      "max_overflow": 10,
      "pool_size": 1000,
      "small_string_length": 255,
      "large_string_length": 32768
    },
    "gotty": {
      "port_redirection": false,
      "bypass_key_prompt": true,
      "port": -1,
      "start_port": 9000,
      "end_port": 9100
    },
    "ldap": {
      "active": false,
      "server": "ldap://domain.ad.company.com",
      "userdn": "domain.ad.company.com",
      "basedn": "DC=domain,DC=ad,DC=company,DC=com",
      "admin_group": "eNMS.Users,network.Admins"
    },
    "mail": {
      "server": "smtp.googlemail.com",
      "port": 587,
      "use_tls": true,
      "username": "eNMS-user",
      "sender": "eNMS@company.com",
      "recipients": "eNMS-user@company.com"
    },
    "mattermost": {
      "url": "https://mattermost.company.com/hooks/i1phfh6fxjfwpy586bwqq5sk8w",
      "channel": "",
      "verify_certificate": true
    },
    "opennms": {
      "opennms_login": "",
      "opennms_devices": "",
      "opennms_rest_api": ""
    },
    "paths": {
      "custom_code": "",
      "custom_properties": "",
      "custom_services": "",
      "playbooks": ""
    },
    "requests": {
      "pool": {
        "pool_connections": 10,
        "pool_maxsize": 100,
        "pool_block": false
      },
      "retries": {
        "total": 2,
        "read": 2,
        "connect": 2,
        "backoff_factor": 0.5
      }
    },
    "slack": {
      "channel": ""
    },
    "syslog": {
      "active": false,
      "address": "0.0.0.0",
      "port": 514
    },
    "tacacs": {
      "active": false,
      "address": ""
    },
    "vault": {
      "active": false,
      "address": "http://127.0.0.1:8200",
      "unseal": false
    },
    "view": {
      "longitude": -96.0,
      "latitude": 33.0,
      "zoom_level": 5,
      "tile_layer": "osm",
      "marker": "Image"
    }
  }

Private configuration
*********************

::

  - export SECRET_KEY=your_secret_key123
  - export VAULT_TOKEN=e1c70d27-7c7f-6f6a-fb18-b0c0382667b7
  - export UNSEAL_VAULT_KEY1=+17lQib+Z/MP5I30Fhd9/yoox9XKzk8bWERv9v3nZ5Ow
  - export UNSEAL_VAULT_KEY2=+17lQib+Z/MP5I30Fhd9/yoox9XKzk8bWERv9v3nZ5Ow
  - export UNSEAL_VAULT_KEY3=+17lQib+Z/MP5I30Fhd9/yoox9XKzk8bWERv9v3nZ5Ow
  - export UNSEAL_VAULT_KEY4=+17lQib+Z/MP5I30Fhd9/yoox9XKzk8bWERv9v3nZ5Ow
  - export UNSEAL_VAULT_KEY5=+17lQib+Z/MP5I30Fhd9/yoox9XKzk8bWERv9v3nZ5Ow
  - export MAIL_PASSWORD=eNMS-user
  - export TACACS_PASSWORD=tacacs_password
  - export OPENNMS_PASSWORD=opennms_password
  - export SLACK_TOKEN=SLACK_TOKEN


Default Examples
----------------

By default, eNMS will create a few examples of each type of object (devices, links, services, workflows...).
If you run eNMS in production, you might want to deactivate this.

To deactivate, set the ``create_examples`` variable to `false`.

Change the documentation base URL
---------------------------------

If you prefer to host your own version of the documentation, you can set the ``documentation_url`` variable in the configuration.
By default, this variable is set to https://enms.readthedocs.io/en/latest/: it points to the online documentation.

