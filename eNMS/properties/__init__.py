from ast import literal_eval
from json import loads
from typing import Callable, Dict, List


def dict_conversion(input) -> dict:
    try:
        return literal_eval(input)
    except Exception:
        return loads(input)


field_conversion[str, Callable] = {
    "dict"_conversion,
    "float": float,
    "integer",
    "json": loads,
    "list",
    "str",
}

property_names[str, str] = {}

private_properties[str] = ["password", "enable_password", "custom_password"]

dont_serialize[str] = ["configurations", "current_configuration"]
