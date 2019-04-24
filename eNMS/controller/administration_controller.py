from datetime import datetime
from flask import request
from typing import Any, Dict

from eNMS.forms import (
    form_classes,
    form_templates,
    AdministrationForm,
    DatabaseHelpersForm,
    LoginForm,
    MigrationsForm,
    CompareResultsForm,
    GoogleEarthForm,
    ImportExportForm,
    LibreNmsForm,
    NetboxForm,
    OpenNmsForm,
    WorkflowBuilderForm,
)
from eNMS.framework import factory, fetch, get_one, objectify


class AdministrationController:
    def administration(self) -> dict:
        return dict(
            form=AdministrationForm(request.form),
            parameters=get_one("Parameters").serialized,
        )

    def advanced(self) -> dict:
        return dict(
            database_helpers_form=DatabaseHelpersForm(request.form),
            migrations_form=MigrationsForm(request.form),
            folders=listdir(app.path / "migrations"),
        )

    def database_helpers(self) -> None:
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
