from collections import Counter

from eNMS.home import bp
from eNMS.classes import classes
from eNMS.functions import fetch_all, fetch_all_visible, get, post
from eNMS.properties import (
    default_diagrams_properties,
    reverse_pretty_names,
    type_to_diagram_properties,
)


@get(bp, "/dashboard")
def dashboard() -> dict:
    on_going = {
        "Running services": len(
            [service for service in fetch_all("Service") if service.status == "Running"]
        ),
        "Running workflows": len(
            [
                workflow
                for workflow in fetch_all("Workflow")
                if workflow.status == "Running"
            ]
        ),
        "Scheduled tasks": len(
            [task for task in fetch_all("Task") if task.status == "Active"]
        ),
    }
    return dict(
        properties=type_to_diagram_properties,
        default_properties=default_diagrams_properties,
        counters={**{cls: len(fetch_all_visible(cls)) for cls in classes}, **on_going},
    )


@post(bp, "/counters/<property>/<type>")
def get_counters(property: str, type: str) -> Counter:
    objects = fetch_all(type)
    if property in reverse_pretty_names:
        property = reverse_pretty_names[property]
    return Counter(map(lambda o: str(getattr(o, property)), objects))
