from apscheduler.schedulers.background import BackgroundScheduler
from flask import Blueprint
from flask_httpauth import HTTPBasicAuth
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from hvac import Client as VaultClient

from eNMS.controller import controller

auth = HTTPBasicAuth()
bp = Blueprint("bp", __name__, template_folder="templates")
csrf = CSRFProtect()
db = SQLAlchemy(session_options={"expire_on_commit": False, "autoflush": False})
login_manager = LoginManager()
login_manager.session_protection = "strong"
mail_client = Mail()
scheduler = BackgroundScheduler(
    {
        "apscheduler.jobstores.default": {
            "type": "sqlalchemy",
            "url": "sqlite:///jobs.sqlite",
        },
        "apscheduler.executors.default": {
            "class": "apscheduler.executors.pool:ThreadPoolExecutor",
            "max_workers": "50",
        },
        "apscheduler.job_defaults.misfire_grace_time": "5",
        "apscheduler.job_defaults.coalesce": "true",
        "apscheduler.job_defaults.max_instances": "3",
    }
)
scheduler.start()
vault_client = VaultClient()
