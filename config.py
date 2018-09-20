from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from os import environ


class Config(object):

    # SQL Alchemy
    SQLALCHEMY_DATABASE_URI = environ.get(
        'ENMS_DATABASE_URL',
        'sqlite:///database.db?check_same_thread=False'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AP Scheduler
    JOBS = []
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url='sqlite:///flask_context.db')
    }
    SCHEDULER_API_ENABLED = True
    SCHEDULER_EXECUTORS = {
        'default': {
            'type': 'threadpool',
            'max_workers': 500
        }
    }

    # GoTTY (webSSH connections)
    # Default: 20 ports reserved from 8080 to 8099)
    # eNMS will use these 20 ports as GoTTY WebSSH terminal
    GOTTY_ALLOWED_PORTS = list(range(8080, 8100))
    
    # 'sshpass' must be installed on the server for the authentication
    GOTTY_AUTHENTICATION = True
    
    # In production, it is likely that the web server (e.g nginx) allows
    # only one port. In that case, the web server can be configured to 
    # redirect the requests to another port, as GoTTY needs its own port to
    # listen to.
    # Example of a redirection from https://eNMS/terminal1 to port 8080 :
    # location /terminal1 {
    # proxy_pass  http://127.0.0.1:8080;
    # } 

    GOTTY_PORT_REDIRECTION = environ.get('GOTTY_PORT_REDIRECTION', False)

    GOTTY_ALLOWED_URLS = [f'terminal{i}' for i in range(3)]


class DebugConfig(Config):
    DEBUG = True
    SECRET_KEY = environ.get('ENMS_SECRET_KEY', 'get-a-real-key')


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = environ.get('ENMS_SECRET_KEY')

    # Vault
    VAULT_ADDR = environ.get('VAULT_ADDR')
    VAULT_TOKEN = environ.get('VAULT_TOKEN')


class SeleniumConfig(Config):
    DEBUG = True
    SECRET_KEY = 'key'
    TESTING = True
    LOGIN_DISABLED = True


config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig,
    'Selenium': SeleniumConfig
}
