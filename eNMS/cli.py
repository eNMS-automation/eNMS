from click import argument, echo
from flask import Flask
from flask.cli import with_appcontext
from json import loads


from eNMS.base.functions import factory, fetch, str_dict


def configure_cli(app: Flask) -> None:
    @app.cli.command()
    @argument("table")
    @argument("name")
    def get(table, name):
        # example: flask get device Washington
        echo(str_dict(fetch(table, name=name).get_properties()))

    @app.cli.command()
    @argument("table")
    @argument("properties")
    def update(table, properties):
        # example: flask update device '{"name": "Aserver", "description": "test"}'
        echo(str_dict(factory(table, **loads(properties)).get_properties()))
