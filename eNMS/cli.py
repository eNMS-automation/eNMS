from click import argument, echo, option
from flask import Flask
from json import loads

from eNMS.concurrency import run_job
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
        result = factory(table, **loads(properties)).get_properties()
        Session.commit()
        echo(controller.str_dict(result))

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
        devices_list = devices.split(",") if devices else []
        devices_list = [fetch("Device", name=name).id for name in devices]
        payload_dict = loads(payload) if payload else {}
        payload_dict["devices"] = devices_list
        job = fetch("Job", name=name)
        results = run_job(job.id, controller.get_time(), **payload_dict)
        Session.commit()
        echo(controller.str_dict(results))
