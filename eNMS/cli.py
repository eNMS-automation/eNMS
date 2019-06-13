from click import argument, echo, option
from flask import Flask
from json import loads

from eNMS.controller import controller
from eNMS.database.functions import delete, factory, fetch


def configure_cli(app: Flask) -> None:
    @app.cli.command(name="fetch")
    @argument("table")
    @argument("name")
    def cli_fetch(table: str, name: str) -> None:
        echo(controller.str_dict(fetch(table, name=name).get_properties()))

    @app.cli.command()
    @argument("table")
    @argument("properties")
    def update(table: str, properties: str) -> None:
        echo(controller.str_dict(factory(table, **loads(properties)).get_properties()))

    @app.cli.command(name="delete")
    @argument("table")
    @argument("name")
    def cli_delete(table: str, name: str) -> None:
        echo(controller.str_dict(delete(table, name=name)))

    @app.cli.command()
    @argument("name")
    @option("--devices")
    @option("--payload")
    def start(name: str, devices: str, payload: str) -> None:
        if devices:
            targets = {fetch("Device", name=name) for name in devices.split(",")}
        else:
            targets = set()
        if payload:
            payload = loads(payload)
        job = fetch("Job", name=name)
        echo(controller.str_dict(job.run(targets=targets, payload=payload)[0]))
