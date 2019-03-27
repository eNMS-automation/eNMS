from click import argument, echo, option
from flask import Flask
from flask.cli import DispatchingApp, pass_script_info
from json import loads
from os import environ
from pathlib import Path
from werkzeug.serving import run_simple

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
        # example: flask start service_name
        # example 2: flask start get_facts --devices Washington,Denver
        # example 3: flask start a_service --payload '{"a": "b"}'
        if devices:
            devices = {fetch("Device", name=name) for name in devices.split(",")}
        else:
            devices = set()
        if payload:
            payload = loads(payload)
        job = fetch("Job", name=name)
        echo(str_dict(job.try_run(targets=devices, payload=payload)[0]))

    @app.cli.command()
    @pass_script_info
    def develop(info, *args):
        # example: flask develop
        app = DispatchingApp(info.load_app)
        path_services = [app._app.path / "eNMS" / "automation" / "services"]
        custom_services_path = environ.get("CUSTOM_SERVICES_PATH")
        if custom_services_path:
            path_services.append(Path(custom_services_path))
        extra_files = [file for path in path_services for file in path.glob("**/*.py")]
        run_simple(
            "0.0.0.0",
            5000,
            app,
            use_reloader=True,
            use_debugger=True,
            extra_files=extra_files,
        )
