from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from flask import Flask, jsonify, request
from json import load
from logging.config import dictConfig
from os import environ
from pathlib import Path
from requests import post
from requests.auth import HTTPBasicAuth


class Scheduler(Flask):

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
        super().__init__(__name__)
        with open(Path.cwd().parent / "setup" / "scheduler.json", "r") as file:
            self.settings = load(file)
        dictConfig(self.settings["logging"])
        self.configure_scheduler()
        self.register_routes()

    @staticmethod
    def aps_date(date):
        if not date:
            return
        date = datetime.strptime(date, "%d/%m/%Y %H:%M:%S")
        return datetime.strftime(date, "%Y-%m-%d %H:%M:%S")

    def configure_scheduler(self):
        self.scheduler = BackgroundScheduler(self.settings["config"])
        self.scheduler.start()

    def register_routes(self):
        @self.route("/delete_job/<job_id>", methods=["POST"])
        def delete_job(job_id):
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            return jsonify(True)

        @self.route("/next_runtime/<task_id>")
        def next_runtime(task_id):
            job = self.scheduler.get_job(task_id)
            if job and job.next_run_time:
                return jsonify(job.next_run_time.strftime("%Y-%m-%d %H:%M:%S"))
            return jsonify("Not Scheduled")

        @self.route("/schedule", methods=["POST"])
        def schedule():
            if request.json["mode"] in ("resume", "schedule"):
                result = self.schedule_task(request.json["task"])
                if not result:
                    return jsonify({"alert": "Cannot schedule in the past."})
                else:
                    return jsonify({"response": "Task resumed.", "active": True})
            else:
                try:
                    self.scheduler.pause_job(request.json["task"]["id"])
                    return jsonify({"response": "Task paused."})
                except JobLookupError:
                    return jsonify({"alert": "There is no such job scheduled."})

        @self.route("/time_left/<task_id>")
        def time_left(task_id):
            job = self.scheduler.get_job(task_id)
            if job and job.next_run_time:
                delta = job.next_run_time.replace(tzinfo=None) - datetime.now()
                hours, remainder = divmod(delta.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                days = f"{delta.days} days, " if delta.days else ""
                return jsonify(f"{days}{hours}h:{minutes}m:{seconds}s")
            return jsonify("Not Scheduled")

    @staticmethod
    def run_service(task_id):
        post(
            f"{environ.get('ENMS_ADDR')}/rest/run_task",
            json=task_id,
            auth=HTTPBasicAuth(environ.get("ENMS_USER"), environ.get("ENMS_PASSWORD")),
            verify=int(environ.get("VERIFY_CERTIFICATE", 1)),
        )

    def schedule_task(self, task):
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
        if not self.scheduler.get_job(task["id"]):
            job = self.scheduler.add_job(
                id=str(task["id"]),
                replace_existing=True,
                func=self.run_service,
                args=[task["id"]],
                **trigger,
            )
        else:
            job = self.scheduler.reschedule_job(str(task["id"]), **trigger)
        return job.next_run_time > datetime.now(job.next_run_time.tzinfo)


scheduler = Scheduler()
