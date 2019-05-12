from ast import literal_eval
from typing import Callable, Dict

field_conversion: Dict[str, Callable] = {
    "dict": literal_eval,
    "float": float,
    "integer": int,
    "list": str,
    "str": str,
}
