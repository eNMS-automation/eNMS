============
Installation
============

Requirements: python 3.6+
(Earlier versions of python not supported.)

Run eNMS in test mode
---------------------

::

 # download the code from github:
 git clone https://github.com/afourmy/eNMS.git
 cd eNMS

 # install the requirements:
 pip install -r requirements.txt

Start eNMS in debugging mode :

::

 # set the FLASK_APP environment variable
 (Windows) set FLASK_APP=app.py
 (Unix) export FLASK_APP=app.py

 # set the FLASK_DEBUG environment variable
 (Windows) set FLASK_DEBUG=1
 (Unix) export FLASK_DEBUG=1

 # run the application
 flask run --host=0.0.0.0

Start eNMS with gunicorn :

::

 # start gunicorn in command-line
 gunicorn --config gunicorn.py app:app

 # or simply
 ./boot.sh

Run eNMS in Production (Unix only)
----------------------------------

To start eNMS in production mode, you must change the value of the  "config_mode" in the config.json file.
The Flask secret key is used for securely signing the session cookie and other security related needs.
In production mode, the secret key is not automatically set to a default value in case it is missing. Therefore, you must configure it yourself:

::

 # set the SECRET_KEY environment variable
 export SECRET_KEY=value-of-your-secret-key


All credentials should be stored in a Hashicorp Vault: the environement variable ``USE_VAULT`` tells eNMS that a Vault has been setup and can be used. This variable is set to ``0`` by default in debug mode, and ``1`` in production mode.
Follow the manufacturer's instructions and options for how to setup a Hashicorp Vault.

If you want to use the Vault in debug mode, you can set it to 1:
 
::

 # set the USE_VAULT environment variable
 export USE_VAULT=1

Once this is done, you must tell eNMS how to connect to the vault:

::

 # set the VAULT_ADDR environment variable
 export VAULT_ADDR=vault-address

 # set the VAULT_TOKEN environment variable
 export VAULT_TOKEN=vault-token

eNMS can also unseal the Vault automatically at start time.
This mechanism is disabled by default. To activate it, you need to:
- set the ``UNSEAL_VAULT`` environement variable to ``1``
- set the UNSEAL_VAULT_KEYx (``x`` in [1, 5]) environment variables :

::

 export UNSEAL_VAULT=1
 # set the UNSEAL_VAULT_KEYx environment variable
 export UNSEAL_VAULT_KEY1=key1
 export UNSEAL_VAULT_KEY2=key2
 etc

You also have to tell eNMS the address of your database by setting the "DATABASE_URL" environment variable.

::

 # set the DATABASE_URL environment variable
 export DATABASE_URL=database-address

In case this environment variable is not set, eNMS will default to using a SQLite database.

LDAP/Active Directory Integration
---------------------------------

The following environment variables (with example values) control how eNMS integrates with LDAP/Active Directory for user authentication. eNMS first checks to see if the user exists locally inside eNMS. If not and if LDAP/Active Directory is enabled, eNMS tries to authenticate against LDAP/AD using the pure python ldap3 library, and if successful, that user gets added to eNMS locally.

::

  Set to 1 to enable LDAP authentication; otherwise 0:
    export USE_LDAP=1
  The LDAP Server URL (also called LDAP Provider URL):
    export LDAP_SERVER=ldap://domain.ad.company.com
  The LDAP distinguished name (DN) for the user. This gets combined inside eNMS as "domain.ad.company.com\\username" before being sent to the server.
    export LDAP_USERDN=domain.ad.company.com
  The base distinguished name (DN) subtree that is used when searching for user entries on the LDAP server. Use LDAP Data Interchange Format (LDIF) syntax for the entries.
    export LDAP_BASEDN=DC=domain,DC=ad,DC=company,DC=com
  The string to match against 'memberOf' attributes of the matched user to determine if the user is allowed to log in.
    export LDAP_ADMIN_GROUP=company.AdminUsers[,group2,group3]

.. note:: Failure to match memberOf attribute output against LDAP_ADMIN_GROUP results in an 403 authentication error. An LDAP user MUST be a member of one of the "LDAP_ADMIN_GROUP" groups to authenticate.
.. note:: Because eNMS saves the user credentials for LDAP and TACACS+ into the Vault, if a user's credentials expire due to password aging, that user needs to login to eNMS in order for the updated credentials to be replaced in Vault storage. In the event that services are already scheduled with User Credentials, these might fail if the credentials are not updated in eNMS.


GIT Integration
---------------

To enable sending device configs captured by configuration management, as well as service and workflow service logs, to GIT for revision control you will need to configure the following:

First, create two separate git projects in your repository. Assign a single GIT userid to have write access to both.

Additionally, the following commands need to be run to properly configure GIT in the eNMS environment. These commands populate ~/.gitconfig:

::

  git config --global user.name "git_username"
  git config --global user.email "git_username_email@company.com"
  git config --global push.default simple

Similarly, if your environment already has an SSH key created for other purposes, you will need to create a new SSH key to register with the GIT server:

::

  ssh-keygen -t rsa -f ~/.ssh/id_rsa.git

And to instruct SSH to use the new key when connecting with the GIT server, create an entry in ~/.ssh/config:

::

  Host git-server
    Hostname git-server.company.com
    IdentityFile ~/.ssh/id_rsa.git
    IdentitiesOnly yes

Additionally, the URLs of each of the GIT server repositories needs to be populated in the Administration Panel of the UI:
  - for the Automation repository to be able tp store the results of services and workflows in git.
  - for the Configurations repository to be able to store device configurations in git.

.. note:: When setting up new groups/projects in GitLab, know that the Master branch by default is protected, and unfortunately in the current version of GitLab, it will not show you that it is protected until a file is added to the repository first. A trick is to press the 'Add README' convenience button in the GitLab UI; this will add a file. Then go to repository, protected branches, and set access rights for Masters and Developers and click 'Unprotect'.


Default Examples
----------------

By default, eNMS will create a few examples of each type of object (devices, links, services, workflows...).
If you run eNMS in production, you might want to deactivate this.

To deactivate, set the ``create_examples`` config parameter to `false`.

Logging
-------

You can configure eNMS as well as Gunicorn log level in the configuration with the `log_level`
variable.

Migration, Backup, and Restore
------------------------------

The eNMS migration system handles exporting the complete database content into JSON files based on eNMS object types.
These migration files are used for migrating from one version of eNMS to the next version. They are also used for Backup and Restore of eNMS.
The migration system is accessed from the :guilabel:`Admin / Administration` or from the ReST API.
Device inventory data is included in the exported migration files, and new devices can be added by importing the Topology Spreadsheet, so these
mechanisms can work together to manage your data:

When creating a new instance of eNMS (backup instance, new version of eNMS):
  - Install eNMS; note that eNMS has an empty database when installed the first time
  - Run the :guilabel:`Admin / Administration / Migration` either from the UI or from the ReST API. Select 'Empty_database_before_import' = True, specify
    the location of the file to import, and select all object types to be imported: "user", "device", "link", "pool", "service", "workflow_edge", "task"
  - Next, run the :guilabel:`Inventory/Import & Export/Import and Export Topology` and specify the Excel Spreadsheet to overlay
    new Device and topology data. Make sure not to select 'replace on import' to prevent overwriting the device data from the migration import.

When backing up eNMS, it is only necessary to perform :guilabel:`Admin / Administration / Migration` either from the UI or from the ReST API.
  - Select a directory name for storing the migration files into, and select all object types to Export
  - the Topology Export of device and link data from :guilabel:`Admin / Administration / Topology Import` and :guilabel:`Admin / Administration / Topology Export` is not needed for Backup.
    It is intended for sharing of device and link data.

Advanced: Migrating Services and Workflows to a new instance with a different inventory:
  - The migration files contain JSON representations of database relationships. Loading a mismatched set of migration files could result in database corruption, so be careful.
  - The Service and Workflow .yaml migration files also contain the list of devices that are selected for each service. If those devices do not exactly exist on the new instance,
    selected devices and pools need to be cleared on all services and workflows before exporting to files. This will allow those services and workflows to be migrated to the new instance.
  - Files needed to migrate: Service.yaml, Workflow.yaml, WorkflowEdge.yaml

If I only want to Import new devices or links to eNMS, perform import of the topology spreadsheet using :guilabel:`Admin / Administration / Topology Import and Export`.

Change the documentation base URL
---------------------------------

If you prefer to host your own version of the documentation, you can set the ``documentation_url`` variable in the configuration.
By default, this variable is set to https://enms.readthedocs.io/en/latest/: it points to the online documentation.
