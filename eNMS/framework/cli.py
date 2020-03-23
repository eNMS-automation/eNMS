from click import argument, echo, option
from json import loads

from eNMS import app
from eNMS.database import Session
from eNMS.database.functions import delete, factory, fetch
from datetime import datetime, timedelta

def configure_cli(flask_app):
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

    @flask_app.cli.command(name="run_service")
    @argument("name")
    @option("--devices")
    @option("--payload")
    def start(name, devices, payload):
        devices_list = devices.split(",") if devices else []
        devices_list = [fetch("device", name=name).id for name in devices_list]
        payload_dict = loads(payload) if payload else {}
        payload_dict["devices"] = devices_list
        service = fetch("service", name=name)
        results = app.run(service.id, **payload_dict)
        Session.commit()
        echo(app.str_dict(results))

    @flask_app.cli.command(name="delete-changelog")
    @option("--keep-last-days", default=15, help="Number of days to keep in the changelog")
    def remove_changelog(keep_last_days):
        """ removes changelog and keeps last 15 days if no other value provided """

        deletion_time = datetime.now() - timedelta(days=keep_last_days)
        kwargs = {}
        kwargs["date_time"] = deletion_time.strftime("%d/%m/%Y %H:%M:%S")
        kwargs["deletion_types"] = ["changelog"]
        app.result_log_deletion(**kwargs)
        print(f"deleted all changelogs up until {deletion_time}")
