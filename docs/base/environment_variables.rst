=====================
Environment Variables
=====================

Below is a reference list of environment variables used to configure eNMS.

Complete List of Environment Variables
--------------------------------------

All sensitive information have to be exported as environment variables.
They are not stored in the configuration file ``config.json``.

::

  - export SECRET_KEY=your_secret_key123
  - export VAULT_TOKEN=e1c70d27-7c7f-6f6a-fb18-b0c0382667b7
  - export UNSEAL_VAULT_KEY1=+17lQib+Z/MP5I30Fhd9/yoox9XKzk8bWERv9v3nZ5Ow
  - export UNSEAL_VAULT_KEY2=+17lQib+Z/MP5I30Fhd9/yoox9XKzk8bWERv9v3nZ5Ow
  - export UNSEAL_VAULT_KEY3=+17lQib+Z/MP5I30Fhd9/yoox9XKzk8bWERv9v3nZ5Ow
  - export UNSEAL_VAULT_KEY4=+17lQib+Z/MP5I30Fhd9/yoox9XKzk8bWERv9v3nZ5Ow
  - export UNSEAL_VAULT_KEY5=+17lQib+Z/MP5I30Fhd9/yoox9XKzk8bWERv9v3nZ5Ow
  - export MAIL_PASSWORD=eNMS-user
  - export TACACS_PASSWORD=tacacs_password
  - export OPENNMS_PASSWORD=opennms_password
  - export SLACK_TOKEN=SLACK_TOKEN