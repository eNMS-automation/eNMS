import os
from eNMS.scheduler.scheduling import (
    Scheduler,
    PrimaryScheduler,
    DelegatingScheduler,
)

WSGI_DELEGATE_SCHEDULING = "WSGI_DELEGATE_SCHEDULING"


class SchedulerFactory:
    @staticmethod
    def create_scheduler(app) -> Scheduler:
        """
        Based on environment variables, determine which type of scheduler should be
        created.  Setting the WSGI_DELEGATE_SCHEDULING variable will create a
        "delegating" scheduler (proxy)

        This is only used for scaling out the number of workers.  The intent is to start
        1. one dedicated, "primary" scheduler
        2. one or more worker applications (via WSGI application) that delegate
           scheduling to that one, dedicated/primary scheduler

        By default, a PrimaryScheduler is created.  The default behavior will match the
        historical one where each application instance has its own, dedicated
        APScheduler.
        """
        if WSGI_DELEGATE_SCHEDULING in os.environ:
            return DelegatingScheduler(app)
        else:
            return PrimaryScheduler(app)
