from multiprocessing import cpu_count
from os import environ

accesslog = "-"
bind = "0.0.0.0:5000"
capture_output = True
enable_stdio_inheritance = True
graceful_timeout = 3000
limit_request_line = 0
loglevel = "debug"
preload_app = True
raw_env = ["TERM=screen"]
timeout = 3000
workers = 2 * cpu_count() + 1 if environ.get("REDIS_ADDR") else 1
