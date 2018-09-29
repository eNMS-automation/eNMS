=======
Web SSH
=======

eNMS uses GoTTY to automatically start an SSH session to any device.
GoTTY is a web SSH solution that can be found on github: https://github.com/yudai/gotty

Installation
------------

There is no need to install GoTTY: it is shipped with eNMS by default in `/eNMS/applications`.
However, you must make sure that the file `gotty` can be executed (`chmod 755 gotty`).

-------
Web SSH

eNMS uses GoTTY to start a web SSH connection to any network device.

"GOTTY_ALLOWED_PORTS" defines which range of ports GoTTY will use to start an SSH session.
eNMS uses a rotation system so that GoTTY will use these ports sequentially to handle all user requests.

eNMS does not by default use the device credentials to automatically log in, but it can be configured to do so with the "GOTTY_AUTHENTICATION" variable. To send in the credentials, eNMS uses "sshpass": you must install "sshpass" on the server if you activate this option.

Allowed ports:
The GOTTY_ALLOWED_PORTS defines which ports are used by GoTTY to start
an SSH session to a device.
The user can access the SSH session on "127.0.0.1:port_number".
Upon starting a connection, eNMS will automatically redirect the user
to that URL.
Default: 20 ports reserved from 8080 to 8099)
eNMS will use these 20 ports as GoTTY WebSSH terminal

Multiplexing:     
By default, each new client that tries to connect to a GoTTY terminal
will have its own SSH session to the target device.
If the port multiplexing option is enabled, clients will all share the
same SSH session instead (they will actually share the same terminal
with tmux)

Port redirection:
In production, it is likely that the web server (e.g nginx) allows
only one port. In that case, the web server can be configured to
redirect the requests to another port, as GoTTY needs its own port to
listen to.
Example of a redirection from https://eNMS/terminal1 to port 8080 :
location /terminal1 {
    proxy_pass  http://127.0.0.1:8080;
}

::

 # enable automatic authentication
 sudo apt-get install sshpass
 export GOTTY_AUTHENTICATION=1

In production, for security reasons, it is possible that only one port is available on the web server. 
In that case, the web server must be configured to redirect the traffic from a given URL to the associated GoTTY port, by configuring the "GOTTY_ALLOWED_URLS" and enabling the redirection by setting "GOTTY_PORT_REDIRECTION" to True.

::

 # enable port redirection
 export GOTTY_PORT_REDIRECTION=1