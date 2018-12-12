from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from hvac import Client as VaultClient
from os import environ
from tacacs_plus.client import TACACSClient

use_vault = int(environ.get('USE_VAULT', False))

login_manager = LoginManager()

auth = HTTPBasicAuth()
db = SQLAlchemy(
    session_options={
        'expire_on_commit': False,
        'autoflush': False
    }
)

mail = Mail()

# Scheduler
scheduler = BackgroundScheduler({
    'apscheduler.jobstores.default': {
        'type': 'sqlalchemy',
        'url': 'sqlite:///jobs.sqlite'
    },
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
        'max_workers': '50'
    },
    'apscheduler.job_defaults.misfire_grace_time': '5',
    'apscheduler.job_defaults.coalesce': 'true',
    'apscheduler.job_defaults.max_instances': '3'
})

# Vault

vault_client = VaultClient()

# Tacacs+
use_tacacs = int(environ.get('USE_TACACS', False))
tacacs_client = TACACSClient(
    environ.get('TACACS_ADDR'),
    49,
    environ.get('TACACS_PASSWORD'),
) if use_tacacs else None

# Syslog
use_syslog = int(environ.get('USE_SYSLOG', False))