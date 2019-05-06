from flask import Blueprint
from flask_httpauth import HTTPBasicAuth
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

auth = HTTPBasicAuth()
bp = Blueprint("bp", __name__, template_folder="templates")
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.session_protection = "strong"
mail_client = Mail()
