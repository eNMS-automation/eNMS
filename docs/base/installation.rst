============
Installation
============

First steps
-----------

::

 # download the code from github:
 git clone https://github.com/afourmy/eNMS.git
 cd eNMS

 # install the requirements:
 pip install -r requirements.txt

Start eNMS in debugging mode
----------------------------

::

 # set the FLASK_APP environment variable
 (Windows) set FLASK_APP=app.py
 (Unix) export FLASK_APP=app.py

 # set the FLASK_DEBUG environment variable
 (Windows) set FLASK_DEBUG=1
 (Unix) export FLASK_DEBUG=1

 # run the application
 flask run --host=0.0.0.0


Start eNMS with gunicorn (better)
---------------------------------

::

 # start gunicorn
 gunicorn --config gunicorn.py app:app


Start eNMS as a docker container (even better)
----------------------------------------------

::

 # download & run the container
 docker run -d -p 5000:5000 --name enms --restart always afourmy/enms

Once eNMS is running, go to http://127.0.0.1:5000
-------------------------------------------------


======================
Run eNMS in Production
======================

To start eNMS in production mode, you must change the value of the environment variable "ENMS_CONFIG_MODE" to "Production".

::

 # set the ENMS_CONFIG_MODE environment variable
 (Windows) set ENMS_CONFIG_MODE=Production
 (Unix) export ENMS_CONFIG_MODE=Production


In production mode, the secret key is not automatically set to a default value in case it is missing. Therefore, you must set it up yourself:

::

 # set the SECRET_KEY environment variable
 (Windows) set SECRET_KEY=value-of-your-secret-key
 (Unix) export SECRET_KEY=value-of-your-secret-key


All credentials in production more are stored in a Vault: you cannot use eNMS in production without first setting up a Vault. Once this is done, you must tell eNMS how to connect to the vault:

::

 # set the VAULT_ADDR environment variable
 (Windows) set VAULT_ADDR=vault-address
 (Unix) export VAULT_ADDR=vault-address

 # set the VAULT_TOKEN environment variable
 (Windows) set VAULT_TOKEN=vault-token
 (Unix) export VAULT_TOKEN=vault-token