from ast import literal_eval
from json import loads


def dict_conversion(input):
    try:
        return literal_eval(input)
    except Exception:
        return loads(input)


field_conversion = {
    "dict": dict_conversion,
    "float": float,
    "int": int,
    "integer": int,
    "json": loads,
    "list": str,
    "str": str,
}

property_names = {}

private_properties = ["password", "enable_password", "custom_password"]

dont_serialize = {"device": ["configuration", "operational_data"]}
