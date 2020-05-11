=================
WebSSH Connection
=================

WebSSH allows the connection to a device via eNMS. Where eNMS handles the establishment of the connection to the device 
using the information stored in the inventory.
eNMS uses GoTTY to automatically start an SSH or Telnet session to a device in the inventory.
GoTTY is a terminal sharing web solution that can be found on github: https://github.com/yudai/gotty.


Installation
------------

GoTTY is shipped with eNMS by default in the following directory ``/eNMS/files/apps``.
You must make sure that the file `gotty` can be executed (``chmod 755 gotty``).

To pass the login passwords to ssh ``sshpass`` has to be installed on the server where eNMS is running.
For the multiplexing feature to work `tmux` has to be installed on the server where eNMS is running.



Port allocation
---------------

By default, eNMS will use the range of ports as defined in the 
:ref:`ssh section <ssh-settings>` in the settings.

eNMS uses a rotation system to allocate these ports sequentially as user requests come in.
You can view this range directly from the web UI, via the :guilabel:`Settings` button on the top of the screen, 
and selecting the ``ssh`` section.



Custom URL
----------

eNMS automatically redirects you to the address and port GoTTY is listening to,
using JavaScript variables ``window.location.hostname`` and ``window.location.protocol``.
If these variables do not redirect to the correct URL, you can tell eNMS which protocol
and URL to use by changing the ``address`` variable in the :ref:`app section <app-settings>` in the settings (just the URL, and 
eNMS will add the port GoTTY is listening to).

Port redirection
----------------

In a production environment, only one port should be allowed (to be exposed) by the HTTP web server. In that case, the reverse proxy must be configured to redirect the requests sent to ``terminal<port_number>`` to ``localhost:<port_number>``.

With Nginx, this can be accomplished with the following `location` block :

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

A full example of the nginx configuration can be found in ``eNMS/files/nginx``.

eNMS does not by default perform any port redirection: you must set the ``port_redirection``
variable to ``true`` in the :ref:`ssh section <ssh-settings>` in the settings to enable it.

Ignore fingerprint prompt
-------------------------

If the remote device is not in ``~/.ssh/known_hosts``, ``ssh`` prompts the user to add ssh fingerprint to ``known_hosts`` file, causing GoTTY to fail. 
To bypass that prompt, you can set the ``bypass_key_prompt`` to ``true`` in the :ref:`ssh section <ssh-settings>` in the settings to run the ``ssh`` command with the options ``-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null``.


Connect to a device
-------------------

The connection dialog shows two options to connect to a device:

- Web Session - allows the interaction with the device using the web browser on a separate tab.
- Desktop Session - will generate and download a shortcut that will open the SSH client on the local PC.
  Requires for the entire port range as defined in the :ref:`ssh section <ssh-settings>` in the settings to be accessible from the client.

From the device management table
********************************

You can connect to a device by clicking on the ``Connect`` button next to each device entry in the :guilabel:`Inventory / Device` table as shown below.

.. image:: /_static/inventory/web_connection/connect_from_device_management.png
   :alt: Connect buttons
   :align: center

The following window will pop up:

.. image:: /_static/inventory/web_connection/connection_parameters.png
   :alt: Connection window
   :align: center

You can configure the following parameters :

- Property used for the connection: by default, eNMS uses the IP address but you can also select to use the name, or any custom property.
- Accept only one client: the first client will be allowed, all others will be rejected when trying to access the terminal URL.
- Share session with all clients: a single process will be shared across all clients with tmux (terminal multiplexing), such that all clients will share the same session (same screen).
- Automatically authenticate (SSH only): eNMS will use the credentials stored in the Vault (production mode) or the database (test mode) to automatically authenticate to the network device. eNMS uses ``sshpass`` for the authentication: it must be installed if you activate the automatic authentication (``sudo apt-get install sshpass``). By default, eNMS uses the user credentials for the authentication (the ones you use to log in to eNMS). However, it can be configured to use the device credentials instead (the credentials that you can specify when creating a new device).
- Protocol: SSH or Telnet.

From the Views
**************

You can also connect to a device via the context menu in the geographical view in :guilabel:`Vizualization / Network View` and :guilabel:`Views / Site View`.
Hover over a device (the cursor will change to an index finger with a device name pop-up), right click and select ``Connect``.


