from collections import Counter
from datetime import datetime
from json.decoder import JSONDecodeError
from sqlalchemy.exc import IntegrityError
from string import punctuation
from typing import Any, List, Set

from eNMS.database import Session
from eNMS.database.functions import count, delete, factory, fetch, fetch_all
from eNMS.models import models
from eNMS.properties.diagram import diagram_classes, type_to_diagram_properties


class BaseController:
    def update_parameters(self, **kwargs):
        Session.query(models["Parameters"]).one().update(**kwargs)
        self.config.update(kwargs)

    def delete_instance(self, cls: str, instance_id: int) -> dict:
        return delete(cls, id=instance_id)

    def get(self, cls: str, id: str) -> dict:
        return fetch(cls, id=id).serialized

    def get_all(self, cls: str) -> List[dict]:
        return [instance.get_properties() for instance in fetch_all(cls)]

    def update(self, cls: str, **kwargs) -> dict:
        try:
            instance = factory(cls, **kwargs)
            return instance.serialized
        except JSONDecodeError:
            return {"error": "Invalid JSON syntax (JSON field)"}
        except IntegrityError:
            return {"error": "An object with the same name already exists"}

    def log(self, severity, content) -> None:
        factory("Log", **{"origin": "eNMS", "severity": severity, "content": content})
        self.log_severity[severity](content)

    def count_models(self):
        return {
            "counters": {
                **{cls: count(cls) for cls in diagram_classes},
                **{
                    "active-Service": count("Service", status="Running"),
                    "active-Workflow": count("Workflow", status="Running"),
                    "active-Task": count("Task", status="Active"),
                },
            },
            "properties": {
                cls: Counter(
                    str(getattr(instance, type_to_diagram_properties[cls][0]))
                    for instance in fetch_all(cls)
                )
                for cls in diagram_classes
            },
        }

    def allowed_file(self, name: str, allowed_modules: Set[str]) -> bool:
        allowed_syntax = "." in name
        allowed_extension = name.rsplit(".", 1)[1].lower() in allowed_modules
        return allowed_syntax and allowed_extension

    def get_time(self) -> str:
        return str(datetime.now())

    def str_dict(self, input: Any, depth: int = 0) -> str:
        tab = "\t" * depth
        if isinstance(input, list):
            result = "\n"
            for element in input:
                result += f"{tab}- {self.str_dict(element, depth + 1)}\n"
            return result
        elif isinstance(input, dict):
            result = ""
            for key, value in input.items():
                result += f"\n{tab}{key}: {self.str_dict(value, depth + 1)}"
            return result
        else:
            return str(input)

    def strip_all(self, input: str) -> str:
        return input.translate(str.maketrans("", "", f"{punctuation} "))
