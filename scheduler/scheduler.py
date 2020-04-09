from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from json import load
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import JSONResponse


class Scheduler(Starlette):
    def __init__(self):
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
            self.settings = load(file)
        self.scheduler = AsyncIOScheduler(self.settings["config"])
        self.scheduler.start()

    def register_routes(self):
        @self.route("/schedule_job", methods=["POST"])
        async def add(request):
            task = await request.json()
            default, trigger = self.scheduler_args(task)
            if not self.scheduler.get_job(self.aps_job_id):
                self.scheduler.add_job(**{**default, **trigger})
            else:
                self.scheduler.reschedule_job(default.pop("id"), **trigger)
            return JSONResponse(True)

        @self.route("/delete_job", methods=["POST"])
        async def delete(request):
            job_id = await request.json()
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            return JSONResponse()

    def run_service(self, task_id):
        post(f"{self.settings['app']}/run_task", data=dumps(task_id))

    def scheduler_args(self, task):
        default = {
            "replace_existing": True,
        }
        if task["scheduling_mode"] == "cron":
            task["periodic"] = True
            expression = task["crontab_expression"].split()
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
                "start_date": self.aps_date("start_date"),
                "end_date": self.aps_date("end_date"),
                "seconds": frequency_in_seconds,
            }
        else:
            task["periodic"] = False
            trigger = {"trigger": "date", "run_date": self.aps_date("start_date")}
        return default, trigger

    @staticmethod
    def run_job():
        print("test")


scheduler = Scheduler()
