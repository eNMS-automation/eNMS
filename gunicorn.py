from os import environ
bind = '0.0.0.0:5000'
workers = 5
accesslog = environ.get('GUNICORN_ACCESS_LOG', '-')
loglevel = environ.get('GUNICORN_LOG_LEVEL', 'debug').lower()
capture_output = True
enable_stdio_inheritance = True
timeout = 1000
graceful_timeout = 1000
limit_request_line = 0