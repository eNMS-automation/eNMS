from click import argument, echo
from flask import Flask
from flask.cli import with_appcontext


from eNMS.base.functions import fetch


def str_dict(input, depth: int = 0) -> str:
    tab = "\t" * depth
    if isinstance(input, list):
        result = "\n"
        for element in input:
            result += f"{tab}- {str_dict(element, depth + 1)}\n"
        return result
    elif isinstance(input, dict):
        result = ""
        for key, value in input.items():
            result += f"\n{tab}{key}: {str_dict(value, depth + 1)}"
        return result
    else:
        return str(input)


def configure_cli(app: Flask) -> None:
    @app.cli.command()
    @argument("table")
    @argument("name")
    def get(table, name):
        echo(fetch(table, name=name).get_properties())
