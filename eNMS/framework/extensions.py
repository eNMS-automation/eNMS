from flask_httpauth import HTTPBasicAuth
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

auth = HTTPBasicAuth()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.session_protection = "strong"
