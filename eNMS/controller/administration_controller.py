from datetime import datetime
from typing import Any, Dict

from eNMS.framework import factory, fetch, objectify


class AdministrationController:
    def database_helpers(self, request) -> None:
        delete_all(*request.form["deletion_types"])
        clear_logs_date = request.form["clear_logs_date"]
        if clear_logs_date:
            clear_date = datetime.strptime(clear_logs_date, "%d/%m/%Y %H:%M:%S")
            for job in fetch_all("Job"):
                job.logs = {
                    date: log
                    for date, log in job.logs.items()
                    if datetime.strptime(date, "%Y-%m-%d-%H:%M:%S.%f") > clear_date
                }
