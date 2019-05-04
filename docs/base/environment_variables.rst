=====================
Environment Variables
=====================

Below is a reference list of environment variables used to configure eNMS. Many of these are described in the Installation section. Some are described within the document in relevant sections. Configurations in the Administration Panel also exist as environment variables for first time startup; if these are desired changed after initial startup and database creation, they must be changed via the Administration Panel UI.

Complete List of Environment Variables
--------------------------------------

::

  - export ENMS_CONFIG_MODE=Production
  - export ENMS_SECRET_KEY=your_secret_key123
  - export USE_VAULT=1
  - export VAULT_ADDR=http://127.0.0.1:8200
  - export VAULT_TOKEN=e1c70d27-7c7f-6f6a-fb18-b0c0382667b7
  - export UNSEAL_VAULT=1
  - export UNSEAL_VAULT_KEY1=nvn7aJgA1wA/z2en/rqeNxU8zxSNcl8bH6L4Voch7LQQ
  - export UNSEAL_VAULT_KEY2=Xndum7gpEykrsRAf6UkaDOSdGFqNMuswggD7zdIYakwI
  - export UNSEAL_VAULT_KEY3=+17lQib+Z/MP5I30Fhd9/yoox9XKzk8bWERv9v3nZ5Ow
  - export ENMS_SERVER_ADDR=https://10.10.10.5
  - export GOTTY_PORT_REDIRECTION=1
  - export GOTTY_BYPASS_KEY_PROMPT=1
  - export GOTTY_START_PORT=9000
  - export GOTTY_END_PORT=9100
  # Uncomment for Postgres Mode:
  # - export ENMS_DATABASE_URL=postgresql://enms:password@localhost:5432/enms
  # - export POSTGRES_PASSWORD=password
  # - export POSTGRES_USER=enms
  # - export POSTGRES_HOST=localhost
  # - export POSTGRES_PORT=5432
  # - export POSTGRES_DB=enms
  # Uncomment for MySQL Mode:
  # - export ENMS_DATABASE_URL=mysql://root:password@localhost/enms
  # Uncomment for SQLite Mode:
  - export ENMS_DATABASE_URL=sqlite:///database.db?check_same_thread=False
  - export SQLITE_WAL_MODE=1     (to enable multiprocessing support in sqlite)
  - export PATH_CUSTOM_PROPERTIES=/home/user/eNMS/eNMS_properties.yml
  - export CREATE_EXAMPLES=0
  - export MAIL_SERVER=smtp.company.com
  - export MAIL_PORT=25
  - export MAIL_USE_TLS=0
  - export MAIL_USERNAME=eNMS-user
  - export MAIL_PASSWORD=eNMS-user
  - export MAIL_SENDER=eNMS@company.com
  - export MAIL_RECIPIENTS=eNMS-user@company.com
  - export MATTERMOST_URL=https://mattermost.company.com/hooks/i1phfh6fxjfwpy586bwqq5sk8w
  - export MATTERMOST_CHANNEL=
  - export MATTERMOST_VERIFY_CERTIFICATE=0
  - export USE_LDAP=1
  - export LDAP_SERVER=ldap://domain.ad.company.com
  - export LDAP_USERDN=domain.ad.company.com
  - export LDAP_BASEDN=DC=domain,DC=ad,DC=company,DC=com
  - export LDAP_ADMIN_GROUP=eNMS.Users,network.Admins
  - export USE_TACACS=1
  - export TACACS_ADDR=122.10.10.10
  - export TACACS_PASSWORD=tacacs_password
  - export USE_SYSLOG=0
  - export SYSLOG_ADDR=0.0.0.0
  - export SYSLOG_PORT=514
  - export CLUSTER=0
  - export CLUSTER_ID=1
  - export CLUSTER_SCAN_SUBNET=192.168.0.0
  - export CLUSTER_SCAN_PROTOCOL=https
  - export CLUSTER_SCAN_TIMEOUT=0.05
  - export DEFAULT_LONGITUDE=-96.0
  - export DEFAULT_LATITUDE=33.0
  - export DEFAULT_ZOOM_LEVEL=5
  - export DEFAULT_VIEW=2D  (or 2DC or 3D)
  - export DEFAULT_MARKER=Circle  (or Image or "Circle Marker")
  - export GIT_AUTOMATION=git@gitlab.company.com:eNMS-group/eNMS-automation-data.git
  - export GIT_CONFIGURATIONS=git@gitlab.company.com:eNMS-group/eNMS-configurations-data.git
  - export POOL_FILTER=All objects
  - export ENMS_LOG_LEVEL=DEBUG
  - export GUNICORN_ACCESS_LOG=logs/app_logs/access.log
  - export GUNICORN_LOG_LEVEL=debug