============================
Web SSH / Telnet (Unix only)
============================

eNMS uses GoTTY to automatically start an SSH or Telnet session to any device.
GoTTY is a terminal sharing web solution that can be found on github: https://github.com/yudai/gotty

Installation
------------

There is no need to install GoTTY: it is shipped with eNMS by default in ``/eNMS/applications``.
However, you must make sure that the file `gotty` can be executed (``chmod 755 gotty``).

Port allocation
---------------

By default, eNMS will use the range of ports [9000, 9099]. eNMS uses a rotation system to allocate these ports sequentially as user requests come in.

You can change this range directly from the web UI, in :guilabel:`admin/parameters` :
 
.. image:: /_static/inventory/web_connection/port_allocation.png
   :alt: GoTTY default range of ports
   :align: center

Custom URL
----------

eNMS automatically redirects you to the address and port GoTTY is listening to, using JavaScript variables ``window.location.hostname`` and ``window.location.protocol``. If these variables do not redirect to the right URL, you can tell eNMS which protocol and URL to use by configuring the ``ENMS_SERVER_ADDR`` environment variable.

::

 # set the ENMS_SERVER_ADDR environment variable
 (Unix) export ENMS_SERVER_ADDR=https://URL (just the URL, and eNMS will add the port GoTTY is listening to)

Port redirection
----------------

In a production environment, only one port should be allowed (to be exposed) by the HTTP web server. In that case, the reverse proxy must be configured to redirect the requests sent to ``terminal<port_number>`` to ``localhost:<port_number>``.

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

eNMS does not by default perform any port redirection: you must set the ``GOTTY_PORT_REDIRECTION`` environment to ``1`` to enable it.

::

 export GOTTY_PORT_REDIRECTION=1

Ignore fingerprint prompt
-------------------------

If the remote device is not in ``~/.ssh/known_hosts``, ``ssh`` prompts the user to add ssh fingerprint to ``known_hosts`` file, causing GoTTY to fail. To bypass that prompt, you can set the ``GOTTY_BYPASS_KEY_PROMPT`` to 1 to run the ``ssh`` command with the options ``-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null``.

::

 export GOTTY_BYPASS_KEY_PROMPT=1

This is equivalent to adding the following lines in ``/etc/ssh_config``:

::

 Host *
     StrictHostKeyChecking no
     UserKnownHostsFile /dev/null

Connect to a device
-------------------

From the device management table
********************************

You can connect to a device by clicking on the ``Connect`` button in :guilabel:`objects/device_management`.

.. image:: /_static/inventory/web_connection/connect_from_device_management.png
   :alt: Connect buttons
   :align: center

The following window will pop up:

.. image:: /_static/inventory/web_connection/connection_parameters.png
   :alt: Connection window
   :align: center

You can configure the following parameters :

- Property used for the connection: by default, eNMS uses the IP address but you can also tell him to use the name, or any custom property.
- Accept only one client: the first client will be allowed, all others will be rejected when trying to access the terminal URL.
- Share session with all clients: a single process will be shared across all clients with tmux (terminal multiplexing), such that all clients will share the same session (same screen).
- Automatically authenticate (SSH only): eNMS will use the credentials stored in the Vault (production mode) or the database (test mode) to automatically authenticate to the network device. eNMS uses ``sshpass`` for the authentication: it must be installed if you activate the automatic authentication (``sudo apt-get install sshpass``). By default, eNMS uses the user credentials for the authentication (the ones you use to log in to eNMS). However, it can be configured to use the device credentials instead (the credentials that you can specify when creating a new device).
- Protocol: SSH or Telnet.

From the views
**************

You can also connect to a device from the geographical or logical view. Double-clicking on a device opens the property panel of that device. This window contains the same ``Connect`` button as in the :guilabel:`objects/device_management` page.

.. image:: /_static/inventory/web_connection/connect_from_view.png
   :alt: Connection window
   :align: center