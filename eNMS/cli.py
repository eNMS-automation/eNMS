from click import argument, echo, option
from flask import Flask
from json import loads

from eNMS.controller import controller
from eNMS.database import Session
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
        factory(table, **loads(properties)).get_properties()
        Session.commit()
        echo(controller.str_dict())

    @app.cli.command(name="delete")
    @argument("table")
    @argument("name")
    def cli_delete(table: str, name: str) -> None:
        device = delete(table, name=name)
        Session.commit()
        echo(controller.str_dict(device))

    @app.cli.command(name="run_job")
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
        results = fetch("Job", name=name).run(targets=targets, payload=payload)[0]
        Session.commit()
        echo(controller.str_dict(results))
