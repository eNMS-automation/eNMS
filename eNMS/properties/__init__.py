from ast import literal_eval
from json import loads
from typing import Callable, Dict, List

field_conversion: Dict[str, Callable] = {
    "dict": literal_eval,
    "float": float,
    "integer": int,
    "json": loads,
    "list": str,
    "str": str,
}

property_names: Dict[str, str] = {}

private_properties: List[str] = ["password", "enable_password", "custom_password"]

ignore_properties: List[str] = ["results", "configurations", "current_configuration", "logs"]
