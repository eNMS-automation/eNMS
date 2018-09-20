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


========
Database
========

You must tell eNMS where to find the address of your database by setting up the "ENMS_DATABASE_URL" environment database.

::

 # set the ENMS_DATABASE_URL environment variable
 (Windows) set ENMS_DATABASE_URL=database-address
 (Unix) export ENMS_DATABASE_URL=database-address


In case this environment variable is not set, eNMS will default to using a SQLite database.

=======
Web SSH
=======

eNMS uses GoTTY to start a web SSH connection to any network device.
GoTTY must be configured in the ``config.py`` file.

::

 # goTTY (webSSH connections)
 # Default: 20 ports reserved from 8080 to 8099)
 # eNMS will use these 20 ports as GoTTY WebSSH terminal
 GOTTY_ALLOWED_PORTS = list(range(8080, 8100))
 # 'sshpass' must be installed on the server for the authentication
 GOTTY_AUTHENTICATION = True

 # In production, it is likely that the web server (e.g nginx) allows
 # only one port. In that case, the web server can be configured to
 # redirect the requests to another port, as GoTTY needs its own port to
 # listen to.
 # Example of a redirection from https://eNMS/terminal1 to port 8080 :
 # location /terminal1 {
 # proxy_pass http://127.0.0.1:8080;
 # }
 GOTTY_WEBSERVER_PORT = 8080
 GOTTY_PORT_REDIRECTION = environ.get('GOTTY_PORT_REDIRECTION', False)
 GOTTY_ALLOWED_URLS = [f'terminal{i}' for i in range(3)]
 # By default, each new client that tries to connect to a GoTTY terminal
 # will have its own SSH session to the target device.
 # If the port multiplexing option is enabled, clients will all share the
 # same SSH session instead (they will actually share the same terminal
 # with tmux)
 # GOTTY_MULTIPLEXING = environ.get('GOTTY_PORT_REDIRECTION', False)

"GOTTY_ALLOWED_PORTS" defines which range of ports GoTTY will use to start an SSH session.
eNMS uses a rotation system so that GoTTY will use these ports sequentially to handle all user requests.

eNMS does not by default use the device credentials to automatically log in, but it can be configured to do so with the "GOTTY_AUTHENTICATION" variable. To send in the credentials, eNMS uses "sshpass": you must install "sshpass" on the server if you activate this option.

::

 # enable automatic authentication
 sudo apt-get install sshpass
 export GOTTY_AUTHENTICATION=1

In production, for security reasons, it is possible that only one port is available on the web server. 
In that case, the web server must be configured to redirect the traffic from a given URL to the associated GoTTY port, by configuring the "GOTTY_ALLOWED_URLS" and enabling the redirection by setting "GOTTY_PORT_REDIRECTION" to True.

::

 # enable port redirection
 export GOTTY_PORT_REDIRECTION=1