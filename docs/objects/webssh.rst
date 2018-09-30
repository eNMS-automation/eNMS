===================
Web SSH (Unix only)
===================

eNMS uses GoTTY to automatically start an SSH session to any device.
GoTTY is a web SSH solution that can be found on github: https://github.com/yudai/gotty

Installation
------------

There is no need to install GoTTY: it is shipped with eNMS by default in ``/eNMS/applications``.
However, you must make sure that the file `gotty` can be executed (``chmod 755 gotty``).

Port allocation
---------------

GoTTY listens to a port provided by eNMS to listen for incoming requests. By default, eNMS will use the range of ports [9000, 9099].
eNMS uses a rotation system to allocate these ports sequentially as user requests come in.
You can change this range directly from the web UI, in :guilabel:`admin/parameters` :
 
.. image:: /_static/objects/webssh/port_allocation.png
   :alt: GoTTY default range of ports
   :align: center

Custom URL
----------

eNMS automatically redirects you to the address and port GoTTY is listening to, using JavaScript variables ``window.location.hostname`` and ``window.location.protocol``. If these variables do not redirect to the right URL, you can tell eNMS which URL and port are the right ones by setting the ``GOTTY_SERVER_ADDR`` in ``config.py``.

::

 # set the GOTTY_SERVER_ADDR environment variable
 (Unix) export GOTTY_SERVER_ADDR=https://URL:8443

Port redirection
----------------

In production, only one port is allowed on the web server. In that case, the reverse proxy must be configured to redirect the requests to ``terminal<port_number>`` to ``localhost:<port_number>``.  (: set it to True to enable it).
eNMS must be made aware of the port redirection by setting the ``GOTTY_PORT_REDIRECTION`` to ``True`` in ``/eNMS/config.py`` (GOTTY_PORT_REDIRECTION is set to False by default: it is disabled).

With Nginx, this can be accomplished with the following `location` :

::

 location ~ ^/terminal(.*)$ {
   proxy_set_header X-Real-IP $remote_addr;
   proxy_set_header X-Forwarded-For $remote_addr;
   proxy_set_header Host $host;
   rewrite ^/terminal(.*)/?$ / break;
   rewrite ^/terminal(.*)/(.*)$ /$2 break;
   proxy_pass http://127.0.0.1:$1;
   proxy_http_version 1.1;
   proxy_set_header Upgrade $http_upgrade;
   proxy_set_header Connection "upgrade";
 }

A full example of nginx configuration can be found in ``eNMS/nginx``.

Connect to a device
-------------------

You can connect to a device by clicking on the ``Connect`` button in :guilabel:`objects/device_management`.

.. image:: /_static/objects/webssh/connect_buttons.png
   :alt: Connect buttons
   :align: center

The following window will pop up:

.. image:: /_static/objects/webssh/connection_parameters.png
   :alt: Connection window
   :align: center

You can configure the following parameters :

- Accept only one client: the first client will be allowed, all others will be rejected when trying to access the terminal URL.
- Share session with all clients: a single process will be shared across all clients with tmux (terminal multiplexing), such that all clients will share the same SSH session (same screen).
- Automatically authenticate: eNMS will use the credentials stored in the Vault (production mode) or the database (test mode) to automatically authenticate to the network device. eNMS uses ``sshpass`` for the authentication: it must be installed if you activate the automatic authentication (``sudo apt-get install sshpass``). By default, eNMS uses the user credentials for the authentication (the ones you use to log in to eNMS). However, it can be configured to use the device credentials instead (the credentials that you can specify when creating a new device).
