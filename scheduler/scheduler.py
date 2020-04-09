from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from json import load, dumps
from os import environ
from pathlib import Path
from requests import post
from starlette.applications import Starlette
from starlette.responses import JSONResponse


class Scheduler(Starlette):

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
            return JSONResponse()

        @self.route("/action", methods=["POST"])
        async def action(request):
            data = await request.json()
            if data["action"] == "resume":
                self.schedule_task(data["task"])
            getattr(self.scheduler, f"{data['action']}_job")(data["job_id"])

        @self.route("/next_runtime/<task_id>", methods=["GET"])
        async def next_runtime(request):
            job = app.scheduler.get_job(request.path_params["task_id"])
            if job and job.next_run_time:
                return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
            return None

        @self.route("/time_left/<task_id>", methods=["GET"])
        async def time_left(request):
            post(f"{scheduler['address']}/time_before_next_run", data=dumps(self.get_properties()))
            job = app.scheduler.get_job(self.aps_job_id)
            if job and job.next_run_time:
                delta = job.next_run_time.replace(tzinfo=None) - datetime.now()
                hours, remainder = divmod(delta.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                days = f"{delta.days} days, " if delta.days else ""
                return f"{days}{hours}h:{minutes}m:{seconds}s"
            return None

    def schedule_task(self, task):
        default, trigger = self.scheduler_args(task)
        if not self.scheduler.get_job(task["aps_job_id"]):
            self.scheduler.add_job(**{**default, **trigger})
        else:
            self.scheduler.reschedule_job(default.pop("id"), **trigger)

    @staticmethod
    def run_service(task_id):
        post(f"{environ.get('ENMS_ADDR')}/run_task", data=dumps(task_id))

    def scheduler_args(self, task):
        default = {"replace_existing": True, "func": self.run_service}
        if task["scheduling_mode"] == "cron":
            task["periodic"] = True
            expression = task["crontab_expression"].split()

            expression[-1] = ",".join(
                self.mapping[day] for day in expression[-1].split(",")
            )
            trigger = {"trigger": CronTrigger.from_crontab(" ".join(expression))}
        elif task["frequency"]:
            task["periodic"] = True
            frequency_in_seconds = (
                int(task["frequency"])
                * {"seconds": 1, "minutes": 60, "hours": 3600, "days": 86400}[
                    task["frequency_unit"]
                ]
            )
            trigger = {
                "trigger": "interval",
                "start_date": self.aps_date(task["start_date"]),
                "end_date": self.aps_date(task["end_date"]),
                "seconds": frequency_in_seconds,
            }
        else:
            task["periodic"] = False
            trigger = {"trigger": "date", "run_date": self.aps_date(task["start_date"])}
        return default, trigger


scheduler = Scheduler()
