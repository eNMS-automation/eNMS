from re import search, sub

from eNMS.functions import fetch, fetch_all, get, post
from eNMS.scheduling import bp


@get(bp, "/calendar", "View")
def calendar() -> dict:
    tasks = {}
    for task in fetch_all("Task"):
        # javascript dates range from 0 to 11, we must account for that by
        # substracting 1 to the month for the date to be properly displayed in
        # the calendar
        date = task.next_run_time
        if not date:
            continue
        python_month = search(r".*-(\d{2})-.*", date).group(1)  # type: ignore
        month = "{:02}".format((int(python_month) - 1) % 12)
        js_date = [
            int(i)
            for i in sub(
                r"(\d+)-(\d+)-(\d+) (\d+):(\d+).*", r"\1," + month + r",\3,\4,\5", date
            ).split(",")
        ]
        tasks[task.name] = {**task.serialized, **{"date": js_date}}
    return dict(tasks=tasks)


@post(bp, "/<action>_task/<int:task_id>", "Edit")
def task_action(action: str, task_id: int) -> bool:
    task = fetch("Task", id=task_id)
    getattr(task, action)()
    return True
