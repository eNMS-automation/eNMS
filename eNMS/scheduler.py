
from apscheduler.schedulers.background import BackgroundScheduler

from eNMS.setup import scheduler as settings


class LocalScheduler:

    def __init__(self):
        self.scheduler = BackgroundScheduler(**settings)
        self.scheduler.start()


class RemoteScheduler:



scheduler_class = RemoteScheduler if settings["remote"]["active"] else LocalScheduler
scheduler = scheduler_class()
