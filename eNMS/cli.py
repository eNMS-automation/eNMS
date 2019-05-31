from click import argument, echo, option
from flask import Flask
from flask.cli import DispatchingApp, pass_script_info, ScriptInfo
from json import loads
from pathlib import Path
from werkzeug.serving import run_simple

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

    @app.cli.command()
    @pass_script_info
    def develop(info: ScriptInfo) -> None:
        app = DispatchingApp(info.load_app)
        path_services = [Path.cwd() / "eNMS" / "automation" / "services"]
        custom_services_path = controller.custom_services_path
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
