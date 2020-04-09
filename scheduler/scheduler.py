from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from json import load
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import JSONResponse


class Scheduler(Starlette):

    def __init__(self, ):
        super().__init__()
        self.configure_scheduler()
        self.register_routes()

    def aps_date(self, datetype):
        date = getattr(self, datetype)
        if date:
            date = datetime.strptime(date, "%d/%m/%Y %H:%M:%S")
            return datetime.strftime(date, "%Y-%m-%d %H:%M:%S")

    def configure_scheduler(self):
        with open(Path.cwd().parent / "setup" / "scheduler.json", "r") as file:
            self.scheduler = AsyncIOScheduler(load(file)["config"])
        self.scheduler.start()

    def register_routes(self):
        @self.route("/add_job", methods=["POST"])
        async def schedule(request):
            self.scheduler.add_job(self.run_job, "interval", seconds=3)
            return JSONResponse(True)

        @self.route("/delete_job", methods=["POST"])
        async def schedule(request):
            data = await request.json()
            return JSONResponse(True)

    def kwargs(self):
        default = {
            "id": self.aps_job_id,
            "func": app.run,
            "replace_existing": True,
            "args": [self.service.id],
            "kwargs": self.run_properties(),
        }
        if self.scheduling_mode == "cron":
            self.periodic = True
            expression = self.crontab_expression.split()
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
            expression[-1] = ",".join(mapping[day] for day in expression[-1].split(","))
            trigger = {"trigger": CronTrigger.from_crontab(" ".join(expression))}
        elif self.frequency:
            self.periodic = True
            frequency_in_seconds = (
                int(self.frequency)
                * {"seconds": 1, "minutes": 60, "hours": 3600, "days": 86400}[
                    self.frequency_unit
                ]
            )
            trigger = {
                "trigger": "interval",
                "start_date": self.aps_date("start_date"),
                "end_date": self.aps_date("end_date"),
                "seconds": frequency_in_seconds,
            }
        else:
            self.periodic = False
            trigger = {"trigger": "date", "run_date": self.aps_date("start_date")}
        return default, trigger

    def schedule(self):
        default, trigger = self.kwargs()
        if not self.get_job(self.aps_job_id):
            self.add_job(**{**default, **trigger})
        else:
            self.reschedule_job(default.pop("id"), **trigger)

    @staticmethod
    def run_job():
        print("test")


scheduler = Scheduler()
