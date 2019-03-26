from click import argument, echo, option
from flask import Flask
from flask.cli import with_appcontext
from json import loads


from eNMS.base.functions import delete, factory, fetch, str_dict


def configure_cli(app: Flask) -> None:
    @app.cli.command(name="fetch")
    @argument("table")
    @argument("name")
    def cli_fetch(table, name):
        # example: flask fetch device Washington
        echo(str_dict(fetch(table, name=name).get_properties()))

    @app.cli.command()
    @argument("table")
    @argument("properties")
    def update(table, properties):
        # example: flask update device '{"name": "Aserver", "description": "test"}'
        echo(str_dict(factory(table, **loads(properties)).get_properties()))

    @app.cli.command(name="delete")
    @argument("table")
    @argument("name")
    def cli_delete(table, name):
        # example: flask delete device Washington
        echo(str_dict(delete(table, name=name)))

    @app.cli.command()
    @argument("name")
    @option("--devices")
    @option("--payload")
    def start(name, devices, payload):
        print(devices, payload)
        # example: flask start service_name
        # example 2: flask start service_name device1,device2,device3
        if devices:
            devices = {fetch("Device", name=name) for name in devices.split(",")}
        else:
            devices = set()
        if payload:
            payload = loads(properties)
        echo(
            str_dict(fetch("Job", name=name).try_run(targets=targets, payload=payload))[
                0
            ]
        )
