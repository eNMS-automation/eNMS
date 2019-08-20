from click import argument, echo, option
from flask import Flask
from json import loads
from typing import Any

from eNMS.controller.concurrency import run_job
from eNMS.database import Session
from eNMS.database.functions import delete, factory, fetch


def configure_cli(flask_app: Flask, app: Any) -> None:
    @flask_app.cli.command(name="fetch")
    @argument("table")
    @argument("name")
    def cli_fetch(table: str, name: str) -> None:
        echo(app.str_dict(fetch(table, name=name).get_properties()))

    @flask_app.cli.command()
    @argument("table")
    @argument("properties")
    def update(table: str, properties: str) -> None:
        result = factory(table, **loads(properties)).get_properties()
        Session.commit()
        echo(app.str_dict(result))

    @flask_app.cli.command(name="delete")
    @argument("table")
    @argument("name")
    def cli_delete(table: str, name: str) -> None:
        device = delete(table, name=name)
        Session.commit()
        echo(app.str_dict(device))

    @flask_app.cli.command(name="run_job")
    @argument("name")
    @option("--devices")
    @option("--payload")
    def start(name: str, devices: str, payload: str) -> None:
        devices_list = devices.split(",") if devices else []
        devices_list = [fetch("Device", name=name).id for name in devices_list]
        payload_dict = loads(payload) if payload else {}
        payload_dict["devices"] = devices_list
        job = fetch("Job", name=name)
        results = run_job(job.id, **payload_dict)
        Session.commit()
        echo(app.str_dict(results))
