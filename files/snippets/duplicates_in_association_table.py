# Provides a straightforward way to reproduce the duplicate rows issue
# in an association table.
# Prevents deleting both part of the association.
# Expected error: "sqlalchemy.orm.exc.StaleDataError: DELETE statement
# on table 'pool_device_association' expected to delete 1 row(s);
# Only 5 were matched."
# flake8: noqa

pool = db.factory("pool", name="A pool")
pool.devices = [db.fetch("device", name="Washington") for _ in range(5)]
db.session.commit()
