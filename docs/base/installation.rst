============
Installation
============

eNMS is designed to run on a **Unix server** with Python **3.6+**.

First steps
-----------

::

 # download the code from github:
 git clone https://github.com/afourmy/eNMS.git
 cd eNMS

 # install the requirements:
 pip install -r build/requirements/requirements.txt

 # set the FLASK_APP environment variable
 export FLASK_APP=app.py

 # start the application with Flask
 flask run --host=0.0.0.0

 # or with gunicorn
 gunicorn --config gunicorn.py app:app

Production mode
---------------

To start eNMS in production mode, you must change the value of the  "config_mode" in the settings.json file, and set the secret
key.

::

 # set the SECRET_KEY environment variable
 export SECRET_KEY=value-of-your-secret-key

All credentials should be stored in a Hashicorp Vault: the settings variable ``active`` under the ``vault`` section of the settings
tells eNMS that a Vault has been setup and can be used.
Follow the manufacturer's instructions and options for how to setup a Hashicorp Vault.

You must tell eNMS how to connect to the Vault with
  - the ``address`` settings variable
  - the ``VAULT_TOKEN`` environment variable

::

 # set the VAULT_TOKEN environment variable
 export VAULT_TOKEN=vault-token

eNMS can also unseal the Vault automatically at start time.
This mechanism is disabled by default. To activate it, you need to:
- set the ``unseal`` settings variable to ``true``
- set the UNSEAL_VAULT_KEYx (``x`` in [1, 5]) environment variables :

::

 export UNSEAL_VAULT_KEY1=key1
 export UNSEAL_VAULT_KEY2=key2
 etc

.. _Settings:

Settings
-------------

The settings are divided into:

- Environment variables for all sensitive data (passwords, tokens, keys). Environment variables are exported
  from Unix with the ``export`` keyword: ``export VARIABLE_NAME=value``.
- Public variables defined in the ``settings.json`` file, and later modifiable from the administration
  panel.

Section ``app``
***************

**Public variables**

- ``address`` (default: ``""``) The address is needed when eNMS needs to provide a link back to the application,
  which is the case with GoTTY and mail notifications. When left empty, eNMS will try to guess the URL. This might
  not work all the time depending on your environment (nginx configuration, proxy, ...)
- ``config_mode`` (default: ``"debug"``) Must be set to "debug" or "production".
- ``create_examples`` (default: ``true``) By default, eNMS will create a network topology and a number of services
  and workflows as an example of what you can do.
- ``documentation_url`` (default: ``"https://enms.readthedocs.io/en/latest/"``) Can be changed if you want to host your
  own version of the documentation locally. Points to the online documentation by default.
- ``git_repository`` (default: ``""``) Git is used as a version control system for device configurations: this variable
  is the address of the remote git repository where eNMS will push all device configurations.

Section ``cluster``
*******************

- ``active`` (default: ``false``)
- ``id`` (default: ``true``)
- ``scan_subnet`` (default: ``"192.168.105.0/24"``)
- ``scan_protocol`` (default: ``"http"``)
- ``scan_timeout`` (default: ``0.05``)

Section ``database``
********************

- ``url`` (default: ``"sqlite:///database.db?check_same_thread=False"``) `SQL Alchemy database URL
  <https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls/>`_, configured
  for SQLite by default.
- ``pool_size`` (default: ``1000``) Number of connections kept persistently in `SQL Alchemy pool
  <https://docs.sqlalchemy.org/en/13/core/pooling.html#sqlalchemy.pool.QueuePool/>`_.
- ``max_overflow`` (default: ``10``) Maximum overflow size of the connection pool.
- ``small_string_length`` (default: ``255``) Length of a small string in the database.
- ``small_string_length`` (default: ``32768``) Length of a large string in the database.

Section ``ldap``
****************

If LDAP/Active Directory is enabled and the user doesn't exist in the database yet, eNMS tries to authenticate against
LDAP/AD using the `ldap3` library, and if successful, that user gets added to eNMS locally.

- ``active`` (default: ``false``) Enable LDAP authentication.
- ``server`` (default: ``"ldap://domain.ad.company.com"``) LDAP Server URL (also called LDAP Provider URL)
- ``userdn`` (default: ``"domain.ad.company.com"``) LDAP Distinguished Name (DN) for the user
- ``basedn`` (default: ``"DC=domain,DC=ad,DC=company,DC=com"``) LDAP base distinguished name subtree that is used when
  searching for user entries on the LDAP server. Use LDAP Data Interchange Format (LDIF) syntax for the entries.
- ``admin_group`` (default: ``"eNMS.Users,network.Admins"``) string to match against 'memberOf' attributes of the
  matched user to determine if the user is allowed to log in.

.. note:: Failure to match memberOf attribute output against LDAP_ADMIN_GROUP results in an 403 authentication error.
  An LDAP user MUST be a member of one of the "LDAP_ADMIN_GROUP" groups to authenticate.
.. note:: Because eNMS saves the user credentials for LDAP and TACACS+ into the Vault, if a user's credentials expire
  due to password aging, that user needs to login to eNMS in order for the updated credentials to be replaced in Vault storage.
  In the event that services are already scheduled with User Credentials, these might fail if the credentials
  are not updated in eNMS.

Section ``logging``
*******************

- ``log_level`` (default: ``"debug"``) Gunicorn log level.
- ``loggers`` (default: ``{"requests": "info", "urllib3": "info"}``) Change the default log levels of eNMS loggers. By default,
eNMS will set the requests and urllib3 library to a log level of "info".

Section ``mail``
****************

  - ``server`` (default: ``"smtp.googlemail.com"``)
  - ``port`` (default: ``587``)
  - ``use_tls`` (default: ``true``)
  - ``username`` (default: ``"eNMS-user"``)
  - ``sender`` (default: ``"eNMS@company.com"``)

Section ``mattermost``
**********************

- ``url`` (default: ``"https://mattermost.company.com/hooks/i1phfh6fxjfwpy586bwqq5sk8w"``)
- ``channel`` (default: ``""``)
- ``verify_certificate`` (default: ``true``)

Section ``paths``
*****************

- ``custom_code`` (default: ``""``)
- ``custom_services`` (default: ``""``) Path to a folder that contains :ref:`Custom Services`.
- ``playbooks`` (default: ``""``)

Section ``requests``
********************

- Pool

  - ``pool_maxsize`` (default: ``10``)
  - ``pool_connections`` (default: ``100``)
  - ``pool_block`` (default: ``false``)

- Retries

    - ``total`` (default: ``2``)
    - ``read`` (default: ``2``)
    - ``connect`` (default: ``2``)
    - ``backoff_factor`` (default: ``0.5``)

Section ``security``
********************

- ``hash_user_passwords`` (default: ``true``) All user passwords are automatically hashed by default.
- ``forbidden_python_libraries`` (default: ``["eNMS","os","subprocess","sys"]``) There are a number of places in the UI where the user
is allowed to run custom python scripts. You can configure which python libraries cannot be imported for security reasons.

Section ``slack``
*****************

- ``channel`` (default: ``""``)

Section ``ssh``
***************

- ``port_redirection`` (default: ``false``)
- ``bypass_key_prompt`` (default: ``true``)
- ``start_port`` (default: ``9000``)
- ``end_port`` (default: ``91000``)

Section ``syslog``
******************

- ``active`` (default: ``false``)
- ``address`` (default: ``"0.0.0.0"``)
- ``port`` (default: ``514``)

Section ``tacacs``
******************

- ``active`` (default: ``false``)
- ``address`` (default: ``""``)
- ``port`` (default: ``514``)

Section ``vault``
*****************

For eNMS to use a Vault to store all sensitive data (user and network credentials), you must set
the ``active`` variable to ``true``, provide an address and export 

**Public variables**

- ``active`` (default: ``false``)
- ``address`` (default: ``"http://127.0.0.1:8200"``)
- ``unseal`` (default: ``false``) Automatically unseal the Vault. You must export the keys as
  environment variables.

**Environment variables**

- ``VAULT_TOKEN``
- ``UNSEAL_VAULT_KEY1``
- ``UNSEAL_VAULT_KEY2``
- ``UNSEAL_VAULT_KEY3``
- ``UNSEAL_VAULT_KEY4``
- ``UNSEAL_VAULT_KEY5``

Section ``view``
****************

- ``longitude`` (default: ``-96.0``)
- ``latitude`` (default: ``33.0``)
- ``zoom_level`` (default: ``5``)
- ``tile_layer`` (default: ``"osm"``)
- ``marker`` (default: ``"Image"``)

Private settings
****************

::

  - SECRET_KEY=secret_key
  - MAIL_PASSWORD=mail_password
  - TACACS_PASSWORD=tacacs_password
  - SLACK_TOKEN=slack_token
