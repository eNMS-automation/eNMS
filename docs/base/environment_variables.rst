=====================
Environment Variables
=====================

Below is a reference list of environment variables used to configure eNMS.

Complete List of Environment Variables
--------------------------------------

::

  - export SECRET_KEY=your_secret_key123
  - export VAULT_ADDR=http://127.0.0.1:8200
  - export VAULT_TOKEN=e1c70d27-7c7f-6f6a-fb18-b0c0382667b7
  - export UNSEAL_VAULT_KEY1=nvn7aJgA1wA/z2en/rqeNxU8zxSNcl8bH6L4Voch7LQQ
  - export UNSEAL_VAULT_KEY2=Xndum7gpEykrsRAf6UkaDOSdGFqNMuswggD7zdIYakwI
  - export UNSEAL_VAULT_KEY3=+17lQib+Z/MP5I30Fhd9/yoox9XKzk8bWERv9v3nZ5Ow
  - export SERVER_ADDR=https://10.10.10.5
  # Uncomment for Postgres Mode:
  # - export DATABASE_URL=postgresql://enms:password@localhost:5432/enms
  # - export POSTGRES_PASSWORD=password
  # - export POSTGRES_USER=enms
  # - export POSTGRES_HOST=localhost
  # - export POSTGRES_PORT=5432
  # - export POSTGRES_DB=enms
  # Uncomment for MySQL Mode:
  # - export DATABASE_URL=mysql://root:password@localhost/enms
  # Uncomment for SQLite Mode:
  - export DATABASE_URL=sqlite:///database.db?check_same_thread=False
  - export PATH_CUSTOM_PROPERTIES=/home/user/eNMS/eNMS_properties.yml
  - export MAIL_PASSWORD=eNMS-user
  - export USE_TACACS=1
  - export TACACS_ADDR=122.10.10.10
  - export TACACS_PASSWORD=tacacs_password
  - export SYSLOG_ADDR=0.0.0.0
  - export SYSLOG_PORT=514
  - export POOL_FILTER=All objects