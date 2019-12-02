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
 pip install -r requirements.txt

 # set the FLASK_APP environment variable
 export FLASK_APP=app.py

 # start the application with Flask
 flask run --host=0.0.0.0

 # or with gunicorn
 gunicorn --config gunicorn.py app:app

Production mode
---------------

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

Configuration
-------------

The configuration is divided into:

- private variables (passwords, tokens, keys) set as environment variables.
- public variables defined in the ``config.json`` file.

Section ``Application``
***********************

- ``address`` (default: ``""``) The address is needed when eNMS needs to provide a link back to the application,
  which is the case with GoTTY and mail notifications. When left empty, eNMS will try to guess the URL. This might
  not work all the time depending on your environment (nginx configuration, proxy, ...)
- ``config_mode`` (default: ``"debug"``) Must be set to "debug" or "production".
- ``create_examples`` (default: ``true``) By default, eNMS will create a network topology and a number of services
  and workflows as an example of what you can do.
- ``documentation_url`` (default: ``"https://enms.readthedocs.io/en/latest/"``) Can be changed if you want to host your
  own version of the documentation locally. Points to the online documentation by default.
- ``log_level`` (default: ``"debug"``) Gunicorn log level.
- ``git_repository`` (default: ``""``) Git is used as a version control system for device configurations: this variable
  is the address of the remote git repository where eNMS will push all device configurations.

Section ``Database``
********************

- ``url`` (default: ``"sqlite:///database.db?check_same_thread=False"``) `SQL Alchemy database URL
  <https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls/>`_, configured
  for SQLite by default.
- ``pool_size`` (default: ``1000``) Number of connections kept persistently in `SQL Alchemy pool
  <https://docs.sqlalchemy.org/en/13/core/pooling.html#sqlalchemy.pool.QueuePool/>`_.
- ``max_overflow`` (default: ``10``) Maximum overflow size of the connection pool.
- ``small_string_length`` (default: ``255``) Length of a small string in the database.
- ``small_string_length`` (default: ``32768``) Length of a large string in the database.

Section ``GoTTY``
*****************

- ``port_redirection`` (default: ``false``)
- ``bypass_key_prompt`` (default: ``true``)
- ``start_port`` (default: ``9000``)
- ``end_port`` (default: ``91000``)

Section ``Cluster``
*******************

- ``active`` (default: ``false``)
- ``id`` (default: ``true``)
- ``scan_subnet`` (default: ``"192.168.105.0/24"``)
- ``scan_protocol`` (default: ``"http"``)
- ``scan_timeout`` (default: ``0.05``)

Section ``LDAP``
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

- Section ``Mail``

  - ``server`` (default: ``"smtp.googlemail.com"``)
  - ``port`` (default: ``587``)
  - ``use_tls`` (default: ``true``)
  - ``username`` (default: ``"eNMS-user"``)
  - ``sender`` (default: ``"eNMS@company.com"``)
  - ``recipients`` (default: ``"eNMS-user@company.com"``)

- Section ``Mattermost``

  - ``url`` (default: ``"https://mattermost.company.com/hooks/i1phfh6fxjfwpy586bwqq5sk8w"``)
  - ``channel`` (default: ``""``)
  - ``verify_certificate`` (default: ``true``)

Section ``OpenNMS``
*******************

- ``address`` (default: ``""``) URL of the REST API.
- ``login`` (default: ``""``) REST login.
- ``devices`` (default: ``""``) URL of the devices to import. This could be a subset of
  all available devices in the API, like
  ``https://demo.opennms.org/opennms/rest/nodes?foreignSource=OpenNMS_ATL``.

- Section ``Paths``

  - ``custom_code`` (default: ``""``)
  - ``custom_properties`` (default: ``""``)
  - ``custom_services`` (default: ``""``) By default, eNMS scans ``eNMS / eNMS / services`` (cf.  for custom
    services, but you can configure a different folder instead.
  - ``playbooks`` (default: ``""``)

- Section ``Requests``

    - Pool

      - ``pool_maxsize`` (default: ``10``)
      - ``pool_connections`` (default: ``100``)
      - ``pool_block`` (default: ``false``)

    - Retries

        - ``total`` (default: ``2``)
        - ``read`` (default: ``2``)
        - ``connect`` (default: ``2``)
        - ``backoff_factor`` (default: ``0.5``)

  - Section ``Slack``

      - ``channel`` (default: ``""``)

  - Section ``Syslog``

    - ``active`` (default: ``false``)
    - ``address`` (default: ``"0.0.0.0"``)
    - ``port`` (default: ``514``)

  - Section ``TACACS``

    - ``active`` (default: ``false``)
    - ``address`` (default: ``""``)
    - ``port`` (default: ``514``)

  - Section ``Vault``

    - ``active`` (default: ``false``)
    - ``address`` (default: ``"http://127.0.0.1:8200"``)
    - ``unseal`` (default: ``false``)

  - Section ``View``

    - ``longitude`` (default: ``-96.0``)
    - ``latitude`` (default: ``33.0``)
    - ``zoom_level`` (default: ``5``)
    - ``tile_layer`` (default: ``"osm"``)
    - ``marker`` (default: ``"Image"``)

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
  - export LIBRENMS_TOKEN=librenms_token
  - export NETBOX_TOKEN=netbox_token
  - export SLACK_TOKEN=SLACK_TOKEN
