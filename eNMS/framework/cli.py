from click import argument, echo, option
from flask import Flask
from json import loads

from eNMS import app
from eNMS.database import Session
from eNMS.database.functions import delete, factory, fetch


def configure_cli(flask_app: Flask):
    @flask_app.cli.command(name="fetch")
    @argument("table")
    @argument("name")
    def cli_fetch(table, name):
        echo(
            app.str_dict(fetch(table, name=name).get_properties(exclude=["positions"]))
        )

    @flask_app.cli.command()
    @argument("table")
    @argument("properties")
    def update(table, properties):
        result = factory(table, **loads(properties)).get_properties(
            exclude=["positions"]
        )
        Session.commit()
        echo(app.str_dict(result))

    @flask_app.cli.command(name="delete")
    @argument("table")
    @argument("name")
    def cli_delete(table, name):
        device = delete(table, name=name)
        Session.commit()
        echo(app.str_dict(device))

    @flask_app.cli.command(name="run_job")
    @argument("name")
    @option("--devices")
    @option("--payload")
    def start(name, devices, payload):
        devices_list = devices.split(",") if devices else []
        devices_list = [fetch("device", name=name).id for name in devices_list]
        payload_dict = loads(payload) if payload else {}
        payload_dict["devices"] = devices_list
        job = fetch("job", name=name)
        results = app.run(job.id, **payload_dict)
        Session.commit()
        echo(app.str_dict(results))
