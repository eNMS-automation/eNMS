from ast import literal_eval
from json import loads
from typing import Callable, Dict, List


def dict_conversion(input: str) -> dict:
    try:
        return literal_eval(input)
    except Exception:
        return loads(input)


field_conversion: Dict[str, Callable] = {
    "dict": dict_conversion,
    "float": float,
    "integer": int,
    "json": loads,
    "list": str,
    "str": str,
}

property_names: Dict[str, str] = {}

private_properties: List[str] = ["password", "enable_password", "custom_password"]

dont_serialize: List[str] = ["configurations", "current_configuration", "positions"]
