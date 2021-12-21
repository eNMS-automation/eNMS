# Installation

eNMS is a Flask web application designed to run on a **Unix server**
with Python **3.6+**. The first section below describes how to get eNMS up
and running quickly in demo mode to help in understanding what it is.  The
following sections give details for setting up a production environment.

## First steps

The first step is to download the application. The user can download the
latest release of eNMS directly to the browser by going to the
[Release section](https://github.com/eNMS-automation/eNMS/releases) of
eNMS github repository.

The other option is to clone the master branch of the git repository
from github:

    # download the code from github:
    git clone https://github.com/eNMS-automation/eNMS.git
    cd eNMS

Once the application is installed, the user must go to the `eNMS` folder and
install eNMS python dependencies:

    # install the requirements:
    pip install -r build/requirements/requirements.txt

Once the requirements have been installed, the user can run the application
with the Flask built-in development server.

    # set the FLASK_APP environment variable
    export FLASK_APP=app.py

    # start the application with Flask
    flask run --host=0.0.0.0

For use in a production environment, it is advised to create a more robust 
environment for the application. The following sections describe the
recommended requirements:

### Database

By default, eNMS will use [SQLite database](https://www.sqlite.org/index.html).
The user can configure a different database from [SQLAlchemy's list of supported
databases](https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls)

For example, for a MySQL database, change the DATABASE_URL environment variable:

    export DATABASE_URL="mysql://root:password@localhost/enms"

### Flask Secret key

Provide a secret key used by Flask to sign sessions:

    # set the SECRET_KEY environment variable
    export SECRET_KEY=value-of-user-secret-key

### WSGI server

A WSGI HTTP server such as gunicorn is required to run eNMS in production, 
instead of the Flask development server.

A recommended configuration file for gunicorn is the main folder: `gunicorn.py`;
it is recommended to run the application with the following command:

    # start the application with gunicorn
    gunicorn --config gunicorn.py app:app

### Hashicorp Vault

All credentials should be stored in a Hashicorp Vault: the settings
variable `use_vault : true` under the `vault` section of the
`setup/settings.json` file tells eNMS that a Vault has been setup.
Follow the manufacturer instructions and options for how to setup a
[Hashicorp Vault](https://www.vaultproject.io/)

Tell eNMS how to connect to the Vault with environment variables:

- `VAULT_ADDRESS`
- `VAULT_TOKEN`


eNMS can also unseal the Vault automatically at start time. This
mechanism is disabled by default. To activate it, one must set
`unseal_vault : true` in `setup/settings.json` and set the UNSEAL_VAULT_KEY
environment variables :

    export UNSEAL_VAULT_KEY1=key1
    export UNSEAL_VAULT_KEY2=key2
    etc

## Environment variables
Environment variables for all sensitive data (passwords, tokens, keys) are
exported from Unix and include:
    
- SECRET_KEY=secret_key
- MAIL_PASSWORD=mail_password
- TACACS_PASSWORD=tacacs_password
- SLACK_TOKEN=slack_token

## Example Systemd Unit and Socket files and Nginx config with proxy-pass

### enms.gunicorn.socket

    [Unit]
    Description=gunicorn socket for enms

    [Socket]
    ListenStream=/run/gunicorn/enms.gunicorn.socket

    [Install]
    WantedBy=sockets.target
    
### enms.gunicorn.service

    [Unit]
    Description=Gunicorn instance to serve enms
    Requires=enms.gunicorn.socket
    After=network.target
    After=mariadb.service
    After=enms.gunicorn_scheduler.service

    [Service]
    PermissionsStartOnly=true
    PIDFile=/run/gunicorn/enms.gunicorn.pid
    User=centos
    Group=centos
    WorkingDirectory=/home/centos/enms
    ExecStartPre=/bin/mkdir -p /run/gunicorn/
    ExecStartPre=/bin/chown -R centos:centos /run/gunicorn/
    Environment="HOSTNAME=HOSTNAME_CHANGEME"
    Environment="SECRET_KEY=SECRET_KEY_CHANGEME"
    Environment="VAULT_ADDR=http://127.0.0.1:8200"
    Environment="VAULT_LOG_LEVEL=info"
    Environment="VAULT_TOKEN=VAULT_TOKEN_CHANGEME"
    Environment="UNSEAL_VAULT_KEY1=VAULT_KEY1_CHANGEME"
    Environment="UNSEAL_VAULT_KEY2=VAULT_KEY2_CHANGEME"
    Environment="UNSEAL_VAULT_KEY3=VAULT_KEY3_CHANGEME"
    Environment="SCHEDULER_ADDR=http://127.0.0.1:8000"
    # To indicate which server a service was run from in Automation/Run table
    Environment="SERVER_NAME=CHANGE_ME"
    Environment="SERVER_ADDR=CHANGE_ME"
    Environment="ENMS_ADDR=https://127.0.0.1"
    Environment="ENMS_PASSWORD=ENMS_PASSWORD_CHANGEME"
    Environment="REDIS_ADDR=127.0.0.1"
    Environment="LDAP_ADDR=ldap://MYCOMPANY_CHANGEME"
    Environment="LDAP_USERDN=MYCOMPANY_CHANGEME"
    Environment="LDAP_BASEDN=DC=my,DC=ad,DC=company,DC=com"
    Environment="TACACS_PASSWORD=CHANGEME"
    Environment="MAIL_PASSWORD=CHANGEME"
    Environment="SLACK_TOKEN=CHANGEME"
    Environment="FLASK_APP=app.py"
    Environment="FLASK_DEBUG=1"
    # PATH to TextFSM repo for Netmiko: https://pynet.twb-tech.com/blog/automation/netmiko-textfsm.html
    Environment="TEXTFSM_PATH=/home/centos/ntc_textfsm/"
    Environment="GUNICORN_ACCESS_LOG=logs/access.log"
    Environment="GUNICORN_LOG_LEVEL=debug"
    Environment="DATABASE_URL=mariadb+mysqldb://root:PASSWORD@localhost/enms?charset=utf8mb4"
    ExecStart=/usr/local/bin/gunicorn --pid /run/gunicorn/enms.gunicorn.pid --worker-tmp-dir /tmpfs-gunicorn --bind unix:/run/gunicorn/enms.gunicorn.socket --chdir /home/centos/enms --config /home/centos/enms/gunicorn.py app:app
    ExecReload=/bin/kill -s HUP $MAINPID
    ExecStop=/bin/kill -s TERM $MAINPID
    TimeoutStopSec=60
    LimitNOFILE=100000

    [Install]
    WantedBy=multi-user.target

### nginx.conf
    user nginx;
    worker_processes auto;
    error_log /var/log/nginx/error.log;
    pid /run/nginx.pid;

    # Load dynamic modules. See /usr/share/nginx/README.dynamic.
    include /usr/share/nginx/modules/*.conf;

    events {
        worker_connections 1024;
    }

    http {
        log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

        access_log  /var/log/nginx/access.log  main;
        sendfile            on;
        tcp_nopush          on;
        tcp_nodelay         on;
        keepalive_timeout   120;
        types_hash_max_size 2048;
        fastcgi_buffers 8 16k;
        fastcgi_buffer_size 32k;
        fastcgi_connect_timeout 900;
        fastcgi_send_timeout 900;
        fastcgi_read_timeout 900;

        include             /etc/nginx/mime.types;
        default_type        application/octet-stream;

        # Load modular configuration files from the /etc/nginx/conf.d directory.
        # See http://nginx.org/en/docs/ngx_core_module.html#include
        # for more information.
        include /etc/nginx/conf.d/*.conf;

        server {
            # port to listen on. Can also be set to an IP:PORT
            listen 443 http2 ssl default_server;
            listen [::]:443 http2 ssl default_server;
            server_name enms-hub;
            server_name_in_redirect on;
            server_tokens off;
            ssl_certificate /etc/ssl/certs/nginx.pem;
            ssl_certificate_key /etc/ssl/private/nginx.key;
            ssl_dhparam /etc/ssl/certs/dhparam.pem;
            client_max_body_size 0;
            client_body_buffer_size 10K;
            client_header_buffer_size 1k;

            ssl_protocols TLSv1.1 TLSv1.2;
            ssl_prefer_server_ciphers on;
            ssl_ciphers "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH";
            ssl_ecdh_curve secp384r1;
            ssl_buffer_size 16k;
            ssl_session_cache shared:SSL:10m;
            ssl_session_timeout 4h; # 4 hours to reuse sessions
            ssl_session_tickets off;
            ssl_stapling off;
            ssl_stapling_verify off;
            resolver CHANGEME valid=300s;
            resolver_timeout 5s;
            # Disable preloading HSTS for now.  One can use the commented out header line that includes
            # the "preload" directive if one understands the implications.
            #add_header Strict-Transport-Security "max-age=63072000; includeSubdomains; preload";
            add_header Strict-Transport-Security "max-age=63072000; includeSubdomains";
            add_header X-Frame-Options DENY;
            add_header X-Content-Type-Options nosniff;

            root  /usr/share/nginx/html;

            # Load configuration files for the default server block.
            #include /etc/nginx/default.d/*.conf;

            # Enable compression for larger files/results
            gzip on;
            gzip_types      text/plain application/xml application/json text/json text/xml;
            gzip_proxied    no-cache no-store private expired auth;
            gzip_min_length 100000;
            gunzip on;

            location / {
                proxy_set_header Host $http_host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_pass http://unix:/run/gunicorn/enms.gunicorn.socket;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "upgrade";
                proxy_connect_timeout 300s;
                # Should match the gunicorn timeout:
                proxy_read_timeout 7200s;
            }

            # Use regex for terminal urls:
            location ~ ^/terminal(.*)$ {
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $remote_addr;
                proxy_set_header Host $host;        
                rewrite ^/terminal(\d*)/(.*)$ /$2 break;
                proxy_pass http://127.0.0.1:$1;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "upgrade";
            }

            error_page 404 /404.html;
                location = /40x.html {
            }
            error_page 500 502 503 504 /50x.html;
                location = /50x.html {
            }

            # Setup enms Documentation link
            location /docs/ {
                proxy_set_header Host $http_host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                alias /home/centos/enms/docs/_build/html/;
            }
        }
        # Added to expose access to the separate/remote scheduler.
        server {
            listen 8000;
            listen [::]:8000;
            server_name enms-scheduler;
            root  /usr/share/nginx/html;
            location / {
                 proxy_set_header Host $http_host;
                 proxy_set_header X-Real-IP $remote_addr;
                 proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                 proxy_set_header X-Forwarded-Proto $scheme;
                 proxy_pass http://unix:/run/gunicorn/enms.gunicorn_scheduler.socket;
                 proxy_connect_timeout 300s; 
                 # Should match the gunicorn timeout:
                 proxy_read_timeout 7200s;
            }
        }
    }

## Settings Files
The application's setup files are located in `/setup/`, and the following
section describe their contents:

### `automation.json`
The `/setup/automation.json` file allows for the customization of some
automation library options, such as Napalm Getters, the default contents
of the parameterized run form for workflows, and the models that one can
access or create from the workflow builder global variables.

### `database.json`
The `/setup/database.json` file contains database and schema configuration
parameters.  Make sure to include a new database engine section here if
switching to another SQLAlchemy supported database variant.

Key parameters to be aware of:

- `pool_size` (default: `1000`) Number of connections kept
  persistently in [SQL Alchemy pool](https://docs.sqlalchemy.org/en/13/core/pooling.html#sqlalchemy.pool.QueuePool/).
- `max_overflow` (default: `10`) Maximum overflow size of the connection
  pool.
- `tiny_string_length` (default: `64`) Length of a tiny string in the database.
- `small_string_length` (default: `255`) Length of a small string in the
  database.
- `small_string_length` (default: `32768`) Length of a large string in the
  database.


### `logging.json`
Logging settings exist in the file `/setup/logging.json`. This
file is directly passed into the Python Logging library, so it uses the
Python3 logger file configuration syntax for the user's version of Python3.
Using this file, the administrator can configure additional loggers and
logger destinations as needed for workflows.

By default, the two loggers are configured:

-   The default logger has handlers for sending logs to the stdout
    console as well as a rotating log file `logs/enms.log`
-   A security logger captures logs for: User A ran Service/Workflow
    B on Devices \[C,D,E\...\] to log file `logs/security.log`

And these can be reconfigured here to forward through syslog to remote
collection if desired. This can also be used as a means to send workflow
data to remote time series databases for dashboarding and longer term
storage of automation results data.

Additionally, the `external loggers` section allows for changing the log
levels for the various libraries used by eNMS.

With multiple gunicorn workers, please consider:

- Using `Python WatchedFileHandler` instead of the `RotatingFileHandler`
- Configuring the LINUX `logrotate` utility to perform the desired log
  rotation

Example logging.json that allows for logging to a time series database in the
workflow's post-processing section or via python snippet service:
``` JSON
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "standard": {
      "format": "%(asctime)s %(levelname)-8s %(message)s"
    },
    "rsyslogdFormatter": {
      "format": "%(filename)s: %(funcName)s: %(message)s"
    },
    "timeseriesSyslogFormatter": {
      "format": "logtype=\"workflow\" %(message)s"
    },
  },
  "handlers": {
    "console": {
      "level": "DEBUG",
      "formatter": "standard",
      "class": "logging.StreamHandler",
      "stream": "ext://sys.stdout"
    },
    "rotation": {
      "level": "DEBUG",
      "formatter": "standard",
      "filename": "logs/enms.log",
      "class": "logging.handlers.WatchedFileHandler"
    },
    "security": {
      "level": "DEBUG",
      "formatter": "rsyslogdFormatter",
      "class": "logging.handlers.SysLogHandler",
      "address": "/dev/log",
      "facility": "local3"
    },
    "timeseries": {
      "level": "INFO",
      "formatter": "timeseriesSyslogFormatter",
      "class": "logging.handlers.SysLogHandler",
      "address": ["X.X.X.X", PortYYYY]
    },
  },
  "loggers": {
    "": {
      "handlers": ["console", "rotation"],
      "level": "DEBUG"
    },
    "security": {
      "handlers": ["security"],
      "level": "DEBUG",
      "change_log": true,
      "service_log": true
    },
    "timeseries": {
      "handlers": ["timeseries"],
      "level": "INFO"
    },
  },
  "external_loggers": {
    "engineio": "error",
    "requests": "info",
    "socketio": "error",
    "urllib3": "info",
    "werkzeug": "error"
  }
}
```

### `properties.json`

The `/setup/properties.json` file includes:

1. Allowing for additional custom properties to be defined in eNMS for
devices and links. In this way, eNMS device inventory can be extended to
include additional columns/fields
2. Allowing for additional custom parameters to be added to services
 and workflows
3. Controlling which parameters and widgets can be seen from the
 Dashboard
4. Controlling which column/field properties are visible in the
 tables for device and link inventory, configuration, pools, as
 well as the service, results, and task browsers

properties.json custom device addition example:

- Keys under `{"custom": { "device": {` name the custom attribute being added.

  - Keys/Value pairs under the newly added custom device attribute device_status.
  
    - \"pretty_name\":\"Default Username\", *device attribute name to be
      displayed in UI*
    - \"type\":\"string\", *data type of attribute*
    - \"default\":\"None\", *default value of attribute*
    - \"private\": true *optional - is attribute hidden from user*
    - \"configuration\": true *optional* - creates a custom 
      \'Inventory/Configurations\' attribute
    - \"log_change\" false *optional* - disables logging when a changes is
      made to attribute
    - \"form\": false *optional* - disables option to edit attribute in
      Device User Interface
    - \"migrate\": false *optional* - choose if attribute should be considered
       for migration
    - \"serialize\": false *optional* - whether it is passed to the front-end
      when the object itself is

- Keys under `"tables" : { "device" : [ {  & "tables" : { "configuration" : [ {`
  Details which attributes to display in these table, add custom attributes here
  
  - Keys/Value pairs for tables
  
    - \"data\":\"device_status\", *attribute created in custom device above*
    - \"title\":\"Device Status\", *name to display in table*
    - \"search\":\"text\", *search type*
    - \"width\":\"80%\", *optional - text alignment, other example 
      \"width\":\"130px\",*
    - \"visible\":false, *default display option*
    - \"orderable\": false *allow user to order by this attribute*

    - Values under `"filtering" : { "device" : [`
      Details which attributes to use for filtering. The user will need to add any
      custom device attributes name to this list for filtering

### `rbac.json`

The `/setup/rbac.json` file allows configuration of which user roles have
access to each of the controls in the UI, which user roles have access to
each of the REST API endpoints.

### `settings.json`
The `/setup/settings.json` file includes the following public variables which
are also modifiable from the administration panel. Changing settings from the
administration panel will cause settings.json to be rewritten if `Write changes
back to  settings.json file` is selected.

#### `app` section

-   `address` (default: `""`) The address is needed when eNMS needs to
    provide a link back to the application, which is the case with webssh
    and mail notifications. When left empty, eNMS will try to guess the
    URL. This might not work consistently depending on the user's environment
    (nginx configuration, proxy, ...)
-   `config_mode` (default: `"debug"`) Must be set to `"debug"` or
    `"production"`.
-   `documentation_url` (default:
    `"https://enms.readthedocs.io/en/latest/"`) Can be changed if one
    want to host one's own version of the documentation locally. Points
    to the online documentation by default.
-   `git_repository` (default: `""`) Git is used as a version control
    system for device configurations: this variable is the address of
    the remote git repository where eNMS will push all device
    configurations.
-   `ip_address`: IP address of this instance of the server
-   `plugin_path`: (default: `"eNMS/plugins"`) location of eNMS plugin
    extensions and customizations
-   `session_timeout_minutes`: (default: `90`)
-   `startup_migration` (default: `"examples"`) Name of the migration to
    load when eNMS starts for the first time.
    -   By default, when eNMS loads for the first time, it will create a
        network topology and a number of services and workflows as
        examples of what the user can do.
    -   One can set the migration to `"default"` instead, in which case
        eNMS will only load what is required for the application to
        function properly.

#### `authentication` section
Lists the methods available for users to login (in order of which they
are shown in the login screen pulldown list).  Default authentication is
specified here.  Because authentication can be custom for many
environments, `eNMS/custom.py` allows the user to customize how the
authentication needs to occur. It can be modified to fit a company's
ldap active directory system, etc.

#### `cluster` section
Section used for detecting other running instances of eNMS.
- `active` (default: `false`)
- `id` (default: `true`)
- `can_subnet` (default: `"192.168.105.0/24"`)
- `scan_protocol` (default: `"http"`)
- `scan_timeout` (default: `0.05`)

#### `mail` section

- `reply_to` (default: `"no_replies@company.com"`)
- `server` (default: `"smtp.googlemail.com"`)
- `port` (default: `587`)
- `use_tls` (default: `true`)
- `username` (default: `"eNMS-user"`)
- `sender` (default: `"eNMS@company.com"`)

#### `mattermost` section

- `url` (default:
  `"https://mattermost.company.com/hooks/i1phfh6fxjfwpy586bwqq5sk8w"`)
- `channel` (default: `""`)
- `verify_certificate` (default: `true`)

#### `paths` section

- `files` (default:`""`) Path to eNMS managed files needed by services
  and workflows. For example, files to upload to devices.
- `custom_code` (default: `""`) Path to custom libraries that can be
  utilized within services and workflows
- `custom_services` (default: `""`) Path to a folder that contains
  `Custom Services`. These services are added to the list of existing
  services in the Automation Panel when building services and workflows.
- `playbooks` (default: `""`) Path to where Ansible playbooks are
  stored so that they are selectable in the Ansible Playbook service.

#### `requests` section

Allows for tuning of the Python Requests library internal structures for
connection pooling. Tuning these might be necessary depending on the
load on eNMS.

- Pool

  - `pool_maxsize` (default: `10`)
  - `pool_connections` (default: `100`)
  - `pool_block` (default: `false`)

- Retries

  - `total` (default: `2`)
  - `read` (default: `2`)
  - `connect` (default: `2`)
  - `backoff_factor` (default: `0.5`)

#### `security` section

- `hash_user_passwords` (default: `true`) All user passwords are
  automatically hashed by default.
- `forbidden_python_libraries` (default:
  `["eNMS","os","subprocess","sys"]`) There are a number of places in
  the UI where the user is allowed to run custom python scripts. The user
  can configure which python libraries cannot be imported for security
  reasons.

#### `slack` section

- `channel` (default: `""`)

#### `ssh` section

- `port_redirection` (default: `false`)
- `bypass_key_prompt` (default: `true`)
- `port` (default: `-1`)
- `start_port` (default: `9000`)
- `end_port` (default: `91000`)

#### `tacacs` section

- `active` (default: `false`)
- `address` (default: `""`)

#### `vault` section

For eNMS to use a Vault to store all sensitive data (user and network
credentials), one must set the `active` variable to `true`, provide an
address and export:

- `active` (default: `false`)
- `unseal` (default: `false`) Automatically unseal the Vault

The keys must be exported as environment variables:

- `VAULT_ADDRESS`
- `VAULT_TOKEN`
- `UNSEAL_VAULT_KEY1`
- `UNSEAL_VAULT_KEY2`
- `UNSEAL_VAULT_KEY3`
- `UNSEAL_VAULT_KEY4`
- `UNSEAL_VAULT_KEY5`

### `themes.json`
The `/setup/themes.json` file exposes some configurable parameters for the
default and dark appearance themes of the application.

### `visualization.json`
The `/setup/visualization.json` file controls the visualization map portion
of the application.  The user can specify whether the visualization defaults
to '2D' mode (recommended for large inventories) or '3D' mode. Also, the
default latitude and longitude of the map can be set here.

Key parameters to note:

- `default` (`"2D"` or `"3D"`)
- `longitude` (default: `-96.0`)
- `latitude` (default: `33.0`)
- `zoom_level` (default: `5`)
- `tile_layer` (default: `"osm"`)
- `marker` (default: `"Circle"`)

## Scheduler

The scheduler used for running tasks at a later time is a web
application that is distinct from eNMS. It can be installed on the same
server as eNMS, or a remote server.

Before running the scheduler, one must configure the following
environment variables so it knows where eNMS is located and what
credentials to authenticate with:

-   `ENMS_ADDR`: URL of the remote server (example:
    `"http://192.168.56.102"`)
-   `ENMS_USER`: eNMS login
-   `ENMS_PASSWORD`: eNMS password

The scheduler is a asynchronous application that must be deployed with
uvicorn :

    cd scheduler
    gunicorn scheduler:scheduler --host 0.0.0.0

### Example Systemd Unit and Socket files

Above nginx.conf sample has a section for eNMS Scheduler

### enms.gunicorn_scheduler.socket

    [Unit]
    Description=Gunicorn/uvicorn socket for eNMS scheduler
    
    [Socket]
    ListenStream=/run/gunicorn/enms.gunicorn_scheduler.socket
    
    [Install]
    WantedBy=sockets.target
    
### enms.gunicorn_scheduler.service

    [Unit]
    Description=Start eNMS Scheduler service using Gunicorn/Uvicorn
    Requires=enms.gunicorn_scheduler.socket
    After=network.target
    After=mariadb.service
    
    [Service]
    PermissionsStartOnly=true
    PIDFile=/run/gunicorn/enms.gunicorn_scheduler.pid
    User=centos
    Group=centos
    WorkingDirectory=/home/centos/enms/eNMS
    ExecStartPre=/bin/mkdir -p /run/gunicorn/
    ExecStartPre=/bin/chown -R centos:centos /run/gunicorn/
    Environment="ENMS_ADDR=https://127.0.0.1"
    Environment="ENMS_PASSWORD=CHANGE_ME"
    Environment="ENMS_USER=admin"
    Environment="VERIFY_CERTIFICATE=0"
    Environment="REDIS_ADDR=127.0.0.1"
    Environment="SCHEDULER_ADDR=http://127.0.0.1:8000"
    Environment="GUNICORN_ACCESS_LOG=/home/centos/enms/logs/access_scheduler.log"
    Environment="GUNICORN_LOG_LEVEL=info"
    Environment="DATABASE_URL=mysql://root:PASSWORD@localhost/enms?charset=utf8"
    ExecStart=/usr/local/bin/gunicorn --pid /run/gunicorn/enms.gunicorn_scheduler.pid --worker-tmp-dir /tmpfs-gunicorn --bind unix:/run/gunicorn/enms.gunicorn_scheduler.socket --chdir /home/centos/enms/scheduler --config /home/centos/enms/scheduler/gunicorn.py scheduler:scheduler
    ExecReload=/bin/kill -s HUP $MAINPID
    ExecStop=/bin/kill -s TERM $MAINPID
    TimeoutStopSec=60
    LimitNOFILE=100000
    
    [Install]
    WantedBy=multi-user.target
    
### `scheduler.json`

The `/setup/scheduler.json` file controls the behavior of the eNMS Scheduler
application.

## Network Data Merge Driver

eNMS features easy access to up-to-date device configurations and 
network data. A service can be configured to periodically collect the latest
configurations direct from devices in a network, after which a backend 
process can leverage Git to synchronize data between all instances of the 
application. These files can be found in the `/network_data/` repository of 
each VM, organized by device name.

Services can also be configured to update only *their instance's* local
repository. This intended functionality has been known to cause merge conflicts
during automatic synchronizations with the shared remote repository.

To prevent this, a merge driver can be used to programmatically
resolve merge conflicts. Such drivers typically utilize a combination of git
attributes, configuration instructions, and custom scripts to function.
Below are all of the components of a proposed driver for the Network Data
repositories:

### `network_data/.gitattributes`

    ...
    * merge=newest
    ...

This line in the attributes file instructs git to associate the merge method 
named "newest" for every file (through the wildcard character) in the repository.

### `network_data/.git/config`

    ...
    [merge "newest"]
        name = Merge by newest commit
        driver = git-merge-newest %O %A %B %L %P master FETCH_HEAD
    [branch "master"]
        mergeoptions = --no-edit
    ...

When added to the existing `.git/config`, these lines define a new merge
strategy and provide the necessary command line arguments, as well as several
placeholder values handled by git. More 
detailed descriptions of these values (along with additional resources on custom
merge drivers in general) are available in [Git's documentation](https://git-scm.com/docs/gitattributes#_defining_a_custom_merge_driver).

### `network_data/git-merge-newest`

    #!/bin/sh
    if git merge-file -p -q "$2" "$1" "$3" > /dev/null;
        then git merge-file "$2" "$1" "$3";
    else
        MINE=$(git log --format="%ct" --no-merges "$6" -1);
        THEIRS=$(git log --format="%ct" --no-merges "$7" -1);
        if [ $MINE -gt $THEIRS ]; then
            git merge-file -q --ours "$2" "$1" "$3" >/dev/null
        else
            git merge-file -q --theirs "$2" "$1" "$3">/dev/null
        fi
    fi

The shell script defines the logic and commands to run when the merge driver
is called. In this case it compares the timestamps from `git log` commands on
the local `master` branch and the contents of `FETCH_HEAD`, accepting the most
recent result.
