from flask import Blueprint
from flask_httpauth import HTTPBasicAuth
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

auth = HTTPBasicAuth()
bp = Blueprint("bp", __name__, template_folder="templates")
csrf = CSRFProtect()
db = SQLAlchemy(session_options={"expire_on_commit": False, "autoflush": False})
login_manager = LoginManager()
login_manager.session_protection = "strong"
mail_client = Mail()
