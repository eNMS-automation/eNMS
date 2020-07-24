============
Installation
============

eNMS is a Flask web application designed to run on a **Unix server** with Python **3.6+**.

.. contents::
  :local:
  :depth: 1

|


First steps
###########

The first step is to download the application. You can download the latest release of eNMS directly from your browser,
by going to the `Release section <https://github.com/eNMS-automation/eNMS/releases>`_ of eNMS github repository.

The other option is to clone the master branch of the git repository from github:

::

 # download the code from github:
 git clone https://github.com/afourmy/eNMS.git
 cd eNMS

Once the application is installed, you must go to the `eNMS` folder and install eNMS python depedencies:

::

 # install the requirements:
 pip install -r build/requirements/requirements.txt

Once the requirements have been installed, you can run the application with Flask built-in development server.

::

 # set the FLASK_APP environment variable
 export FLASK_APP=app.py

 # start the application with Flask
 flask run --host=0.0.0.0

|

Production mode
###############

Database
********

By default, eNMS will use an SQLite database (`sqlite:///database.db`). You can configure a different database with the
`DATABASE_URL` environment variable
(see `SQL Alchemy database URL <https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls>`_)

For example, for a MySQL database, the variable could be:

::

 export DATABASE_URL="mysql://root:password@localhost/enms"


Secret key
**********

You need to configure the secret key used by Flask to sign sessions

::

 # set the SECRET_KEY environment variable
 export SECRET_KEY=value-of-your-secret-key

WSGI server
***********

You must use a WSGI HTTP server like gunicorn to run eNMS instead of Flask development server.

You can find a configuration file for gunicorn in the main folder (`gunicorn.py`), and run the application with the 
following command:

::

 # start the application with gunicorn
 gunicorn --config gunicorn.py app:app

Hashicorp Vault
***************

All credentials should be stored in a Hashicorp Vault: the settings variable ``active`` under the ``vault`` section of
the settings tells eNMS that a Vault has been setup and can be used.
Follow the manufacturer's instructions and options for how to setup a Hashicorp Vault.

You must tell eNMS how to connect to the Vault with
  - the ``VAULT_ADDRESS`` environment variable
  - the ``VAULT_TOKEN`` environment variable

::

 # set the VAULT_ADDRESS environment variable
 export VAULT_ADDRESS=url of the vault
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
########

The ``/setup/settings.json`` file includes:

- Environment variables for all sensitive data (passwords, tokens, keys). Environment variables are exported
  from Unix with the ``export`` keyword: ``export VARIABLE_NAME=value``. Environment variables include:

::

    - SECRET_KEY = secret_key
    - MAIL_PASSWORD = mail_password
    - TACACS_PASSWORD = tacacs_password
    - SLACK_TOKEN = slack_token

- Public variables defined in the ``settings.json`` file, and later modifiable from the administration
  panel. Note that changing settings from the administration panel do not currently cause the settings.json file
  to be rewritten.

.. _app-settings:

Settings ``app`` section
**************************

- ``address`` (default: ``""``) The address is needed when eNMS needs to provide a link back to the application,
  which is the case with GoTTY and mail notifications. When left empty, eNMS will try to guess the URL. This might
  not work consistently depending on your environment (nginx configuration, proxy, ...)
- ``config_mode`` (default: ``"debug"``) Must be set to "debug" or "production".
- ``startup_migration`` (default: ``"examples"``) Name of the migration to load when eNMS starts for the first time.
By default, when eNMS loads for the first time, it will create a network topology and a number of services and workflows
as examples of what you can do. You can set the migration to ``"default"`` instead, in which case eNMS will only load what
is required for the application to function properly.
- ``documentation_url`` (default: ``"https://enms.readthedocs.io/en/latest/"``) Can be changed if you want to host your
  own version of the documentation locally. Points to the online documentation by default.
- ``git_repository`` (default: ``""``) Git is used as a version control system for device configurations: this variable
  is the address of the remote git repository where eNMS will push all device configurations.

Settings ``cluster`` section
*******************************

- ``active`` (default: ``false``)
- ``id`` (default: ``true``)
- ``scan_subnet`` (default: ``"192.168.105.0/24"``)
- ``scan_protocol`` (default: ``"http"``)
- ``scan_timeout`` (default: ``0.05``)

Settings ``database`` section
*******************************

- ``pool_size`` (default: ``1000``) Number of connections kept persistently in `SQL Alchemy pool
  <https://docs.sqlalchemy.org/en/13/core/pooling.html#sqlalchemy.pool.QueuePool/>`_.
- ``max_overflow`` (default: ``10``) Maximum overflow size of the connection pool.
- ``small_string_length`` (default: ``255``) Length of a small string in the database.
- ``small_string_length`` (default: ``32768``) Length of a large string in the database.

Settings ``ldap`` section
****************************

If LDAP/Active Directory is enabled and the user doesn't exist in the database yet, eNMS tries to authenticate against
LDAP/AD using the `ldap3` library, and if successful, that user gets added to eNMS locally.

- ``active`` (default: ``false``) Enable LDAP authentication.
- ``server`` (default: ``"ldap://domain.ad.company.com"``) LDAP Server URL (also called LDAP Provider URL)
- ``userdn`` (default: ``"domain.ad.company.com"``) LDAP Distinguished Name (DN) for the user
- ``basedn`` (default: ``"DC=domain,DC=ad,DC=company,DC=com"``) LDAP base distinguished name subtree that is used when
  searching for user entries on the LDAP server. Use LDAP Data Interchange Format (LDIF) syntax for the entries.
- ``admin_group`` (default: ``"eNMS.Users,network.Admins"``) string to match against 'memberOf' attributes of the
  matched user to determine if the user is allowed to log in.

.. note:: Failure to match memberOf attribute output against ``admin_group`` results in a valid ldap user
  within the ``basedn`` being denied access on login. If a memberOf attribute matches the ``admin_group``, they
  will be given Admin permissions.
.. note:: eNMS does not store the credentials of LDAP and TACACS users; however, those users are listed in the
  Admin / Users panel.

Settings  ``mail`` section
****************************

  - ``server`` (default: ``"smtp.googlemail.com"``)
  - ``port`` (default: ``587``)
  - ``use_tls`` (default: ``true``)
  - ``username`` (default: ``"eNMS-user"``)
  - ``sender`` (default: ``"eNMS@company.com"``)

Settings ``mattermost`` section
**********************************

- ``url`` (default: ``"https://mattermost.company.com/hooks/i1phfh6fxjfwpy586bwqq5sk8w"``)
- ``channel`` (default: ``""``)
- ``verify_certificate`` (default: ``true``)

Settings  ``paths`` section
*****************************

- ``files`` (default:``""``) Path to eNMS managed files needed by services and workflows. For example, files to upload
  to devices.
- ``custom_code`` (default: ``""``) Path to custom libraries that can be utilized within services and workflows
- ``custom_services`` (default: ``""``) Path to a folder that contains :ref:`Custom Services`. These services are added
  to the list of existing services in the Automation Panel when building services and workflows.
- ``playbooks`` (default: ``""``) Path to where Ansible playbooks are stored so that they are
  choosable in the Ansible Playbook service.

Settings ``requests`` section
********************************

Allows for tuning of the Python Requests library internal structures for connection pooling. Tuning
these might be necessary depending on the load on eNMS.

- Pool

  - ``pool_maxsize`` (default: ``10``)
  - ``pool_connections`` (default: ``100``)
  - ``pool_block`` (default: ``false``)

- Retries

    - ``total`` (default: ``2``)
    - ``read`` (default: ``2``)
    - ``connect`` (default: ``2``)
    - ``backoff_factor`` (default: ``0.5``)

Settings  ``security`` section
*********************************

- ``hash_user_passwords`` (default: ``true``) All user passwords are automatically hashed by default.
- ``forbidden_python_libraries`` (default: ``["eNMS","os","subprocess","sys"]``) There are a number of places in the UI
  where the user is allowed to run custom python scripts. You can configure which python libraries cannot be imported
  for security reasons.

Settings ``slack`` section
****************************

- ``channel`` (default: ``""``)

.. _ssh-settings:

Settings ``ssh`` section
************************

- ``port_redirection`` (default: ``false``)
- ``bypass_key_prompt`` (default: ``true``)
- ``port`` (default: ``-1``)
- ``start_port`` (default: ``9000``)
- ``end_port`` (default: ``91000``)
- ``enabled``

    - ``web`` (default: ``true``)   Enables device terminal connections in a browser tab
    - ``desktop`` (default: ``true``)  Enables device terminal connections from your desktop software that tunnels
      through eNMS to the device

Settings ``syslog`` section
*****************************

- ``active`` (default: ``false``)
- ``address`` (default: ``"0.0.0.0"``)
- ``port`` (default: ``514``)

Settings ``tacacs`` section
*****************************

- ``active`` (default: ``false``)
- ``address`` (default: ``""``)

Settings ``vault`` section
****************************

For eNMS to use a Vault to store all sensitive data (user and network credentials), you must set
the ``active`` variable to ``true``, provide an address and export

**Public variables**

- ``active`` (default: ``false``)
- ``unseal`` (default: ``false``) Automatically unseal the Vault. You must export the keys as
  environment variables.

**Environment variables**

- ``VAULT_ADDRESS``
- ``VAULT_TOKEN``
- ``UNSEAL_VAULT_KEY1``
- ``UNSEAL_VAULT_KEY2``
- ``UNSEAL_VAULT_KEY3``
- ``UNSEAL_VAULT_KEY4``
- ``UNSEAL_VAULT_KEY5``

Settings ``view`` section
***************************

Controls the default view for where the map is initially displayed in the Visualization panels

- ``longitude`` (default: ``-96.0``)
- ``latitude`` (default: ``33.0``)
- ``zoom_level`` (default: ``5``)
- ``tile_layer`` (default: ``"osm"``)
- ``marker`` (default: ``"Image"``)


Logging file
############

Logging settings exist in separate file: ``/setup/logging.json``. This file is directly passed into the Python Logging library,
so it uses the Python3 logger file configuration syntax for your version of Python3. Using this file, the administrator
can configure additional loggers and logger destinations as needed for workflows.

By default, the two loggers are configured:
  - The default logger has handlers for sending logs to the stdout console as well as a rotating log file ``logs/enms.log``
  - A security logger captures logs for: User A ran Service/Workflow B on Devices [C,D,E...] to log file ``logs/security.log``

And these can be reconfigured here to forward through syslog to remote collection if desired.

Additionally, the ``external loggers`` section allows for changing the log levels for the various libraries used by eNMS


Properties file
###############

The ``/setup/properties.json`` file includes:

  1. Allowing for additional custom properties to be defined in eNMS for devices. In this way, eNMS device inventory can be extended to include additional columns/fields
  #. Allowing for additional custom parameters to be added to services and workflows
  #. Controlling which parameters and widgets can be seen from the Dashboard
  #. Controlling which column/field properties are visible in the tables for device and link inventory, configuration, pools, as well as the service, results, and task browsers

|

properties.json custom device addition example:
    - Keys under ``{"custom": { "device": {``
        - name the custom attribute being added.
        - Keys/Value pairs under the newly added custom device attribute device_status.
            - "pretty_name":"Default Username", *device attribute name to be displayed in UI*
            - "type":"string", *data type of attribute*
            - "default":"None", *default value of attribute*
            - "private": true *optional - is attribute hidden from user*
            - "configuration": true *optional - creates a custom 'Inventory/Configurations' attribute
            - "log_change" false *optional - disables logging when a changes is made to attribute
            - "form": false *optional - disables option to edit attribute in Device User Interface
            - "migrate": fasle *optional - choose if attribute should be consdered for migration
            - "serialize": false *optional - whether it is passed to the front-end when the object itself is
    - Keys under ``"tables" : { "device" : [ {  & "tables" : { "configuration" : [ {``
        - Details which attributes to display in these table, add custom attributes here
        - Keys/Value pairs for tables
            - "data":"device_status", *attribute created in custom device above*
            - "title":"Device Status", *name to display in table*
            - "search":"text", *search type*
            - "width":"80%", *optional - text alignment, other example "width":"130px",*
            - "visible":false, *default display option*
            - "orderable": false *allow user to order by this attribute*
    - Values under ``"filtering" : { "device" : [``
        - details which attributes to use for filtering
        - you will need to add any custom device attributes name to this list for filtering

RBAC file
#########

The ``/setup/rbac.json`` file allows configuration of:

  - Which user roles have access to each of the controls in the UI
  - Which user roles have access to each of the REST API endpoints

Environment variables
#####################

  - SECRET_KEY=secret_key
  - MAIL_PASSWORD=mail_password
  - TACACS_PASSWORD=tacacs_password
  - SLACK_TOKEN=slack_token

Scheduler
---------

The scheduler used for running tasks at a later time is a web application that is distinct from eNMS.
It can be installed on the same server as eNMS, or a remote server.

Before running the scheduler, you must configure the following environment variables so it knows where
eNMS is located and what credentials to authenticate with:

- ``ENMS_ADDR``: URL of the remote server (example: ``"http://192.168.56.102"``)
- ``ENMS_USER``: eNMS login
- ``ENMS_PASSWORD``: eNMS password

The scheduler is a asynchronous application that must be deployed with uvicorn :

::

 cd scheduler
 uvicorn scheduler:scheduler --host 0.0.0.0

