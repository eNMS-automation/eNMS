from flask_assets import Environment
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_httpauth import HTTPBasicAuth
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

assets = Environment()
auth = HTTPBasicAuth()
cache = Cache()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.session_protection = "strong"
mail_client = Mail()
toolbar = DebugToolbarExtension()
