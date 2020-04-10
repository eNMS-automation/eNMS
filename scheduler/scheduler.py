from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from json import load
from os import environ
from pathlib import Path
from requests import post
from requests.auth import HTTPBasicAuth
from starlette.applications import Starlette
from starlette.responses import JSONResponse


class Scheduler(Starlette):

    days = {
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

    seconds = {"seconds": 1, "minutes": 60, "hours": 3600, "days": 86400}

    def __init__(self):
        super().__init__()
        self.configure_scheduler()
        self.register_routes()

    @staticmethod
    def aps_date(date):
        if not date:
            return
        date = datetime.strptime(date, "%d/%m/%Y %H:%M:%S")
        return datetime.strftime(date, "%Y-%m-%d %H:%M:%S")

    def configure_scheduler(self):
        with open(Path.cwd().parent / "setup" / "scheduler.json", "r") as file:
            self.settings = load(file)
        self.scheduler = AsyncIOScheduler(self.settings["config"])
        self.scheduler.start()

    def register_routes(self):
        @self.route("/schedule", methods=["POST"])
        async def add(request):
            self.schedule_task(await request.json())
            return JSONResponse(True)

        @self.route("/job", methods=["DELETE"])
        async def delete(request):
            job_id = await request.json()
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            return JSONResponse(True)

        @self.route("/action", methods=["POST"])
        async def action(request):
            data = await request.json()
            if data["action"] == "resume":
                self.schedule_task(data["task"])
            getattr(self.scheduler, f"{data['action']}_job")(data["job_id"])
            return JSONResponse(True)

        @self.route("/next_runtime/{task_id}")
        async def next_runtime(request):
            job = self.scheduler.get_job(request.path_params["task_id"])
            if job and job.next_run_time:
                return JSONResponse(job.next_run_time.strftime("%Y-%m-%d %H:%M:%S"))
            return JSONResponse("Not Scheduled")

        @self.route("/time_left/{task_id}")
        async def time_left(request):
            job = self.scheduler.get_job(request.path_params["task_id"])
            if job and job.next_run_time:
                delta = job.next_run_time.replace(tzinfo=None) - datetime.now()
                hours, remainder = divmod(delta.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                days = f"{delta.days} days, " if delta.days else ""
                return JSONResponse(f"{days}{hours}h:{minutes}m:{seconds}s")
            return JSONResponse("Not Scheduled")

    def schedule_task(self, task):
        default = {
            "replace_existing": True,
            "func": self.run_service,
            "id": task["aps_job_id"],
            "args": [task["id"]],
        }
        if task["scheduling_mode"] == "cron":
            crontab = task["crontab_expression"].split()
            crontab[-1] = ",".join(self.days[day] for day in crontab[-1].split(","))
            trigger = {"trigger": CronTrigger.from_crontab(" ".join(crontab))}
        elif task["frequency"]:
            trigger = {
                "trigger": "interval",
                "start_date": self.aps_date(task["start_date"]),
                "end_date": self.aps_date(task["end_date"]),
                "seconds": int(task["frequency"])
                * self.seconds[task["frequency_unit"]],
            }
        else:
            trigger = {"trigger": "date", "run_date": self.aps_date(task["start_date"])}
        if not self.scheduler.get_job(task["aps_job_id"]):
            self.scheduler.add_job(**{**default, **trigger})
        else:
            self.scheduler.reschedule_job(default.pop("id"), **trigger)

    @staticmethod
    def run_service(task_id):
        auth = HTTPBasicAuth(environ.get("ENMS_USER"), environ.get("ENMS_PASSWORD"))
        run_task_url = f"{environ.get('ENMS_ADDR')}/rest/run_task"
        print(run_task_url, task_id)
        post(run_task_url, json=task_id, auth=auth)


scheduler = Scheduler()
