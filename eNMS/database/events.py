from sqlalchemy import event, inspect
from sqlalchemy.orm.collections import InstrumentedList

from eNMS.database import db
from eNMS.models import models
from eNMS.database.properties import private_properties


def configure_events(app):
    @event.listens_for(db.base, "after_insert", propagate=True)
    def log_instance_creation(mapper, connection, target):
        if hasattr(target, "name"):
            app.log("info", f"CREATION: {target.type} '{target.name}'")

    @event.listens_for(db.base, "before_delete", propagate=True)
    def log_instance_deletion(mapper, connection, target):
        name = getattr(target, "name", target.id)
        app.log("info", f"DELETION: {target.type} '{name}'")

    @event.listens_for(db.base, "before_update", propagate=True)
    def log_instance_update(mapper, connection, target):
        state, changelog = inspect(target), []
        for attr in state.attrs:
            hist = state.get_history(attr.key, True)
            if (
                getattr(target, "dont_track_changes", False)
                or getattr(state.class_, attr.key).info.get("dont_track_changes")
                or attr.key in private_properties
                or not hist.has_changes()
            ):
                continue
            change = f"{attr.key}: "
            if type(getattr(target, attr.key)) == InstrumentedList:
                if hist.deleted:
                    change += f"DELETED: {hist.deleted}"
                if hist.added:
                    change += f"{' / ' if hist.deleted else ''}ADDED: {hist.added}"
            else:
                change += (
                    f"'{hist.deleted[0] if hist.deleted else None}' => "
                    f"'{hist.added[0] if hist.added else None}'"
                )
            changelog.append(change)
        if changelog:
            name, changes = getattr(target, "name", target.id), " | ".join(changelog)
            app.log("info", f"UPDATE: {target.type} '{name}': ({changes})")

    if app.settings["vault"]["active"]:

        @event.listens_for(models["service"].name, "set", propagate=True)
        def vault_update(target, new_value, old_value, *_):
            path = f"secret/data/{target.type}/{old_value}/password"
            data = app.vault_client.read(path)
            if not data:
                return
            app.vault_client.write(
                f"secret/data/{target.type}/{new_value}/password",
                data={"password": data["data"]["data"]["password"]},
            )
