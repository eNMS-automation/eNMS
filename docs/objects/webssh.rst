=======
Web SSH
=======

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

Port redirection
----------------

In production, only one port is allowed on the web server. In that case, the reverse proxy must be configured to redirect the requests to ``terminal<port_number>`` to ``localhost:<port_number>``.
eNMS must be made aware of the port redirection by setting the ``GOTTY_PORT_REDIRECTION`` to ``True`` in ``/eNMS/config.py``.

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

Connection parameters
---------------------

eNMS does not by default use the device credentials to automatically log in, but it can be configured to do so. To send in the credentials, eNMS uses "sshpass": you must install "sshpass" on the server if you activate this option.

Multiplexing:     
By default, each new client that tries to connect to a GoTTY terminal
will have its own SSH session to the target device.
If the port multiplexing option is enabled, clients will all share the
same SSH session instead (they will actually share the same terminal
with tmux)
