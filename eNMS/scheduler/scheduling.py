import json
import random
import functools
from os import getenv
from time import sleep
from datetime import date, time, timezone, timedelta
from abc import abstractmethod
from dateutil.parser import isoparse
from base64 import urlsafe_b64encode
from urllib3.util.url import Url, parse_url
from requests import Session as RequestSession
from requests.adapters import HTTPAdapter

from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from concurrent.futures import ThreadPoolExecutor

MAX_IDLE_ATTEMPTS = 300
DEFAULT_SCHEDULER_PORT = 5005
DEFAULT_SCHEDULER_CONFIGURATION = {
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
    "scheduler_http_port": "5005",
}


def get_authorization_token():
    return getenv("INTERNAL_API_KEY", "Not-valid-API-key")


def custom_serialize(obj: object):
    """
    This started with the basic apscheduler.job.Job class - it uses the __slots__
    mechanism and does not maintain its own internal dictionary of attributes (as a
    lightweight object).

    A few other customizations were added so that we could serialize the internal
    APScheduler objects as JSON.

    References:
    1. https://stackoverflow.com/questions/10252010/serializing-class-instance-to-json/
        42611918
    2. https://stackoverflow.com/questions/15721363/preserve-python-tuples-with-json
    3. https://gist.github.com/majgis/4200488
    """
    if isinstance(obj, date) or isinstance(obj, time) or isinstance(obj, timezone):
        dt = obj.isoformat()
        return dt
    elif isinstance(obj, timedelta):
        return {
            "days": obj.days,
            "seconds": obj.seconds,
            "microseconds": obj.microseconds,
        }
    if hasattr(obj, "__tuple__"):
        return tuple(obj["items"])

    cls = type(obj)
    props = None
    # The '__slots__' check was initially added for the APScheduler Job class;
    # also applied to DateTrigger.
    if "__slots__" in dir(cls):
        # Added: fix for DateTrigger which defines a single __slots__ as a single
        # string rather than a list.
        slots = [cls.__slots__] if isinstance(cls.__slots__, str) else cls.__slots__
        props = filter(lambda p: not p.startswith("_"), slots)
    # The second case was added for another APScheduler internal class, pytz.timezone
    elif "pytz.tzfile" in str(cls):
        return obj.zone
    # General fallback if the __dict__ attribute is not present
    elif not hasattr(obj, "__dict__"):
        props = filter(lambda p: not p.startswith("_"), dir(obj))
    if props is not None:
        result = {}
        for x in props:
            result[x] = getattr(obj, x)
        return result
    # Default
    else:
        return obj.__dict__


class Scheduler:
    """
    Abstract base class that defines the Scheduling functionality that needed by the
    system - as provided today by the APScheduler module.  This will help allow for
    alternate implementation(s).

    Note: currently, several methods return an APScheduler-defined type  (i.e., Job).
    We are not remapping this type today.  As needed, we will adjust individual
    properties.

    Note that there is some extra serialization support needed to send the Job
    instances over the wire.
    """

    def start(self, **kwargs):
        pass

    @abstractmethod
    def pause(self):
        pass

    @abstractmethod
    def resume(self):
        pass

    @abstractmethod
    def status(self) -> {"state": int}:
        pass

    @abstractmethod
    def get_job(self, job_id, jobstore=None) -> Job:
        pass

    @abstractmethod
    def get_jobs(self, jobstore=None):
        pass

    @abstractmethod
    def add_job(self, func, *args, **kwargs) -> Job:
        pass

    @abstractmethod
    def modify_job(self, **kwargs) -> Job:
        pass

    @abstractmethod
    def reschedule_job(self, job_id, **kwargs) -> Job:
        pass

    @abstractmethod
    def pause_job(self, **kwargs) -> Job:
        pass

    @abstractmethod
    def resume_job(self, **kwargs) -> Job:
        pass

    @abstractmethod
    def remove_job(self, job_id, **kwargs):
        pass

    def _adjust_job_input(self, **kwargs):
        """
        This is an internal support method - it exists to be able to transform an
        incoming job if supplied in the same format as the result of get_job().

        This allows us to send a payload that matches what the results of get_job
        actually look like back into the API.  It will manually look up the apscheduler
        trigger type (i.e., 'interval', 'cron', 'date')
        """
        trigger = kwargs.pop("trigger", None)
        if not isinstance(trigger, str) and trigger is not None:
            trigger, trigger_args = self._lookup_trigger(trigger)
            kwargs = {**kwargs, **trigger_args}
        kwargs.pop("func", None)
        kwargs.pop("func_ref", None)
        return trigger, kwargs

    def _fixup_job_result(self, job):
        """
        When we take the internal Job object and convert it to JSON as a result (or
        input into a REST API), make any adjustments here.

        For the 'crontab'-style jobs, we are going to convert the internal
        CrontabTrigger back into a crontab expression (string).

        This will help serialize the CronTrigger the REST API.
        """
        if job is not None:
            if isinstance(job.trigger, CronTrigger):
                job.trigger = {"cron": self._convert_cron_trigger(job.trigger)}
        return job

    def _convert_cron_trigger(self, cron_trigger):
        """
        This will convert the internal APScheduler CronTrigger into a crontab string
        :param cron_trigger: CronTrigger
        :return: str
        """
        fields = cron_trigger.fields
        mapping = {
            "sun": "0",
            "mon": "1",
            "tue": "2",
            "wed": "3",
            "thu": "4",
            "fri": "5",
            "sat": "6",
            "*": "*",
        }
        cron_expression = " ".join(str(fields[index]) for index in [6, 5, 2, 1])
        cron_expression += " " + ",".join(
            mapping[day] for day in str(fields[4]).split(",")
        )
        return cron_expression

    @staticmethod
    def _lookup_trigger(trigger_args):
        """
        Based on the type of "trigger" (value), different dictionary values are needed.
        This will trim out left-over parameters not needed by the APScheduler API.
        """
        if isinstance(trigger_args, CronTrigger):
            trigger_args = {"cron": trigger_args}
        keys = trigger_args.keys()
        if "cron" in keys or "crontab_expression" in keys:
            cron = trigger_args.pop("cron") or trigger_args.pop("crontab_expression")
            # This replicates code from models/scheduling.py - need to fix this.
            if isinstance(cron, str):
                expression = cron.split()
                mapping = {
                    "0": "sun",
                    "1": "mon",
                    "2": "tue",
                    "3": "wed",
                    "4": "thu",
                    "5": "fri",
                    "6": "sat",
                    "7": "sun",
                    "*": "*",
                }
                expression[-1] = ",".join(
                    mapping[day] for day in expression[-1].split(",")
                )
                cron = CronTrigger.from_crontab(" ".join(expression))
            if not isinstance(cron, CronTrigger):
                raise Exception(
                    "Could not convert arg to CronTrigger; must specify 'cron'"
                    " or 'crontab_expression'"
                )
            # This is what I think I need to return so we get back to this style of
            # API per APScheduler docs:
            # scheduler.add_job(job_function, CronTrigger.from_crontab("10 * * * 0,2))
            return cron, {}
        if "date" in keys:
            trigger_args = {
                key: val for key, val in trigger_args.items() if key in ["run_date"]
            }
            return "date", trigger_args
        if "interval" in keys:
            if "interval" in trigger_args.keys():
                interval = trigger_args.pop("interval")
                trigger_args = {
                    key: val
                    for key, val in interval.items()
                    if key in ["weeks", "days", "hours", "minutes", "seconds", "jitter"]
                }
            return "interval", trigger_args
        raise Exception("not supported trigger type")


class PrimaryScheduler(Scheduler):
    """
    This class implements our wrapper abstract Scheduler class
    and defers all implementation to the internal APScheduler instance.

    Today, there should only every be one of these PrimaryScheduler that is running
    (active) at a time. Currently, this only supports vertical scaling (up).

    Horizontal (out) scaling support could be added with some coordination between
    multiple masters (i.e., an is_active() check and HTTP redirect to clients to
    whichever master is active).

    This would require additional coordination between "primary" schedulers to
    negotiate which one is "active."
    """

    def __init__(self, app):
        self.app = app
        self.config = (
            app.settings.get("scheduler", None) or DEFAULT_SCHEDULER_CONFIGURATION
        )
        self.scheduler = BackgroundScheduler(self.config)

    def start(self):
        """ Start the AP Background Scheduler """
        self.scheduler.start()
        return {"success": True}

    def pause(self):
        self.scheduler.pause()
        return {"success": True}

    def resume(self):
        self.scheduler.resume()
        return {"success": True}

    def status(self) -> {"state": int}:
        return {"state": self.scheduler.state}

    def get_job(self, job_id, jobstore=None) -> Job:
        return self._fixup_job_result(self.scheduler.get_job(job_id, jobstore))

    def get_jobs(self, jobstore=None):
        jobs = self.scheduler.get_jobs(jobstore)
        d = [self._fixup_job_result(j) for j in jobs]
        return d

    def add_job(self, **kwargs) -> Job:
        # We need to change the original 'func' argument to be something meaningful to
        # this process. For the current application, this appears to be sufficient.
        func = self.app.run
        trigger, kwargs = self._adjust_job_input(**kwargs)
        return self._fixup_job_result(
            self.scheduler.add_job(func=func, trigger=trigger, **kwargs)
        )

    def modify_job(self, **kwargs) -> Job:
        job_id = kwargs.pop("id", None) or kwargs.pop("job_id", None)
        trigger, kwargs = self._adjust_job_input(**kwargs)
        return self._fixup_job_result(self.scheduler.modify_job(job_id, **kwargs))

    def reschedule_job(self, job_id, **kwargs) -> Job:
        trigger, kwargs = self._adjust_job_input(**kwargs)
        return self._fixup_job_result(
            self.scheduler.reschedule_job(job_id, **{"trigger": trigger, **kwargs})
        )

    def remove_job(self, job_id, **kwargs):
        self._fixup_job_result(
            self.scheduler.remove_job(job_id, jobstore=kwargs.get("jobstore", None))
        )
        return {"success": True}

    def pause_job(self, job_id, **kwargs) -> Job:
        return self._fixup_job_result(
            self.scheduler.pause_job(job_id, jobstore=kwargs.get("jobstore", None))
        )

    def resume_job(self, job_id, **kwargs) -> Job:
        return self._fixup_job_result(self.scheduler.resume_job(job_id, **kwargs))


class JsonObjectDict(dict):
    """
    Convert a plain JSON object to one that supports lookup by either name (dictionary)
    or attribute.

    Reference: https://goodcode.io/articles/python-dict-object/
    """

    def __init__(self, initial):
        super(JsonObjectDict, self).__init__(initial)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)


def clear_idle(func):
    """
    This decorator applies only to the DelegatingScheduler, below.
    It is used as a housekeeping item to:
       a) retrieve an initial list of Jobs from the PrimaryScheduler,
       b) to keep this list "reasonably" up-to-date
       c) allow for 'disabling' of updating the job list if it is not being used (idle)
    """

    @functools.wraps(func)
    def refresh_job_data(self, *args, **kwargs):
        self._idle_counter = 0
        if not self.running:
            self.get_jobs()
            self.start()
        return func(self, *args, **kwargs)

    return refresh_job_data


class DelegatingScheduler(Scheduler):
    """
    The 'remote' scheduler delegates to the single LocalScheduler; i.e., it is a
    REST-based proxy and will use the REST API to make calls to the LocalScheduler.

    Note: any REST API calls made to the 'remote' scheduler will also be proxied to the
    PrimaryScheduler.
    """

    def __init__(self, app):
        self.app = app
        # This might be a different session use case than the session defined in base.py
        self.session = RequestSession()
        for protocol in ("http", "https"):
            self.session.mount(
                f"{protocol}://",
                HTTPAdapter(max_retries=1, **self.app.settings["requests"]["pool"]),
            )
        self.session.headers = {
            "content-type": "application/json",
            "x-internal-rest-api-key": urlsafe_b64encode(
                get_authorization_token().encode("utf-8")
            ),
        }
        self.session.verify = False
        self.timeout = 10
        self.config = (
            app.settings.get("scheduler", None) or DEFAULT_SCHEDULER_CONFIGURATION
        )
        url = parse_url(self.app.settings["app"]["address"] or "http://localhost:5000")
        port = self.config.get("scheduler_http_port", None) or DEFAULT_SCHEDULER_PORT
        self.address = str(
            Url(
                url.scheme,
                url.auth,
                url.host,
                port,
                f"{(url.path or '')+'/rest/scheduler'}",
            )
        )
        self.date_time_properties = ["next_run_time", "start_date", "end_date"]
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._jobs = dict()
        self.running = False
        self._idle_counter = 0
        self.inactivity_timeout = (
            None  # placeholder for when we 'stop' the continuous polling
        )

    def _fixup_job_json(self, job):
        """
        The 'raw' JSON object needs two conversions back for the Job object:
        1. It needs to be in an attribute form (@see JsonObjectDict, above)
        2. It needs some of its attributes to be converted back into proper Python
           types from JSON strings (i.e., date_time)
        """
        result = JsonObjectDict(job)
        status = getattr(result, "status_code", None)
        if status is not None:
            if int(status) >= 400:
                raise Exception(getattr(result, "error", "Unknown error"))
        for date_time_name in self.date_time_properties:
            temp = getattr(result, date_time_name, None)
            if temp:
                result[date_time_name] = isoparse(temp)
        # Always update the cache when this is done.
        # This guarantees any modified job is available immediately.
        if not hasattr(result, "id"):
            raise Exception("Error, expected job result to have the 'id' property")
        self._jobs[result.id] = result
        return result

    def _fixup_job_data(self, job_data):
        # @TODO: this almost identical to the Scheduler._fixup_job_result.
        if (
            job_data is not None
            and isinstance(job_data, dict)
            and "trigger" in job_data.keys()
        ):
            if isinstance(job_data["trigger"], CronTrigger):
                job_data["trigger"] = {
                    "cron": self._convert_cron_trigger(job_data["trigger"])
                }
        return job_data

    def _update_jobs(self):
        """
        This function will run periodically (unless a period of inactivity occurs)
        """
        if not self.running:
            return
        try:
            sleep(
                random.randrange(400, 1200, 100) / 1000.0
            )  # ask frequently but not at the same time for all workers
            self._idle_counter += 1
            self.get_jobs()
        finally:
            # If nobody is actively using the scheduling features, allow this routine
            # activity to stop
            if self._idle_counter > MAX_IDLE_ATTEMPTS:
                self.running = False
            if self.running:
                self.executor.submit(self._update_jobs)

    def start(self):
        self._idle_counter = 0
        self.running = True
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=1)
        self.executor.submit(self._update_jobs)

    def stop(self):
        self.running = False
        if self.executor is not None:
            self.executor.shutdown(False)
        self.executor = None

    def pause(self):
        return self.session.post(
            f"{self.address}/pause",
            timeout=self.timeout,
            allow_redirects=True,
            data=json.dumps({}),
        ).json()

    def resume(self):
        return self.session.post(
            f"{self.address}/resume",
            timeout=self.timeout,
            allow_redirects=True,
            data=json.dumps({}),
        ).json()

    def status(self):
        return self.session.post(
            f"{self.address}/status",
            timeout=self.timeout,
            allow_redirects=True,
            data=json.dumps({}),
        ).json()

    @clear_idle
    def get_job(self, job_id) -> object:
        """
        When originally implemented, a direct proxy to the PrimaryScheduler was simply
        far too slow. So, instead, we are going to cache results and update them
        periodically.
        """
        return self._jobs.get(job_id, None)

    def get_jobs(self):
        jobs = self.session.post(
            f"{self.address}/get_jobs", data=json.dumps({}, default=custom_serialize)
        ).json()
        return [self._fixup_job_json(j) for j in jobs]

    @clear_idle
    def add_job(self, **kwargs) -> object:
        self._fixup_job_data(kwargs)
        return self._fixup_job_json(
            self.session.post(
                f"{self.address}/add_job",
                timeout=self.timeout,
                allow_redirects=True,
                data=json.dumps(kwargs, default=custom_serialize),
            ).json()
        )

    @clear_idle
    def modify_job(self, **kwargs) -> object:
        self._fixup_job_data(kwargs)
        return self._fixup_job_json(
            self.session.post(
                f"{self.address}/modify_job",
                timeout=self.timeout,
                allow_redirects=True,
                data=json.dumps(kwargs, default=custom_serialize),
            ).json()
        )

    @clear_idle
    def reschedule_job(self, job_id, **kwargs) -> object:
        self._fixup_job_data(kwargs)
        return self._fixup_job_json(
            self.session.post(
                f"{self.address}/reschedule_job",
                timeout=self.timeout,
                allow_redirects=True,
                data=json.dumps({"job_id": job_id, **kwargs}, default=custom_serialize),
            ).json()
        )

    @clear_idle
    def remove_job(self, job_id, **kwargs):
        result = self.session.post(
            f"{self.address}/remove_job",
            timeout=self.timeout,
            allow_redirects=True,
            data=json.dumps({"job_id": job_id, **kwargs}, default=custom_serialize),
        ).json()
        return result

    @clear_idle
    def pause_job(self, job_id, **kwargs) -> object:
        return self._fixup_job_json(
            self.session.post(
                f"{self.address}/pause_job",
                timeout=self.timeout,
                allow_redirects=True,
                data=json.dumps({"job_id": job_id, **kwargs}, default=custom_serialize),
            ).json()
        )

    @clear_idle
    def resume_job(self, job_id, **kwargs) -> object:
        return self._fixup_job_json(
            self.session.post(
                f"{self.address}/resume_job",
                timeout=self.timeout,
                allow_redirects=True,
                data=json.dumps({"job_id": job_id, **kwargs}, default=custom_serialize),
            ).json()
        )
