============
Installation
============

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

 # start gunicorn
 gunicorn --config gunicorn.py app:app


Start eNMS as a docker container :

::

 # download & run the container
 docker run -d -p 5000:5000 --name enms --restart always afourmy/enms

Once eNMS is running, you can go to http://127.0.0.1:5000, create an account and log in.

Run eNMS in Production (Unix only)
----------------------------------

To start eNMS in production mode, you must change the value of the environment variable "ENMS_CONFIG_MODE" to "Production".

::

 # set the ENMS_CONFIG_MODE environment variable
 export ENMS_CONFIG_MODE=Production

The Flask secret key is used for securely signing the session cookie and other security related needs.
In production mode, the secret key is not automatically set to a default value in case it is missing. Therefore, you must configure it yourself:

::

 # set the ENMS_SECRET_KEY environment variable
 export ENMS_SECRET_KEY=value-of-your-secret-key


All credentials in production more are stored in a Hashicorp Vault: you cannot use eNMS in production without first setting up a Vault.
Once this is done, you must tell eNMS how to connect to the vault:

::

 # set the VAULT_ADDR environment variable
 export VAULT_ADDR=vault-address

 # set the VAULT_TOKEN environment variable
 export VAULT_TOKEN=vault-token

eNMS can also unseal the Vault automatically at start time.
This mechanism is disabled by default. To activate it, you need to:
  - set the ``UNSEAL_VAULT`` variable in ``config.py`` to ``True``
  - set the UNSEAL_VAULT_KEYx (``x`` in [1, 5]) environment variables :

::

 # set the UNSEAL_VAULT_KEYx environment variable
 export UNSEAL_VAULT_KEY1=key1
 export UNSEAL_VAULT_KEY2=key2
 etc

You also have to tell eNMS the address of your database by setting the "ENMS_DATABASE_URL" environment variable.

::

 # set the ENMS_DATABASE_URL environment variable
 export ENMS_DATABASE_URL=database-address

In case this environment variable is not set, eNMS will default to using a SQLite database.
