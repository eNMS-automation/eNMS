from collections import defaultdict
from flask_login import current_user
from operator import attrgetter, itemgetter
from pathlib import Path
from re import search, sub
from threading import Thread
from uuid import uuid4

from eNMS import app
from eNMS.database import db
from eNMS.models import models


class AutomationController:
    def add_edge(self, workflow_id, subtype, source, destination):
        now = app.get_time()
        workflow = db.fetch("workflow", id=workflow_id, rbac="edit")
        workflow_edge = self.update(
            "workflow_edge",
            rbac=None,
            **{
                "name": now,
                "workflow": workflow_id,
                "subtype": subtype,
                "source": source,
                "destination": destination,
            },
        )
        db.session.commit()
        workflow.last_modified = now
        return {"edge": workflow_edge, "update_time": now}

    def calendar_init(self, type):
        results = {}
        for instance in db.fetch_all(type):
            if getattr(instance, "workflow", None):
                continue
            date = getattr(instance, "next_run_time" if type == "task" else "runtime")
            python_month = search(r".*-(\d{2})-.*", date)
            if not python_month:
                continue
            month = "{:02}".format((int(python_month.group(1)) - 1) % 12)
            start = [
                int(i)
                for i in sub(
                    r"(\d+)-(\d+)-(\d+) (\d+):(\d+).*",
                    r"\1," + month + r",\3,\4,\5",
                    date,
                ).split(",")
            ]
            results[instance.name] = {"start": start, **instance.serialized}
        return results

    def clear_results(self, service_id):
        for result in db.fetch(
            "run", all_matches=True, allow_none=True, service_id=service_id
        ):
            db.session.delete(result)
