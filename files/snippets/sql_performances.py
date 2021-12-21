# Uses eNMS fetch, factory and delete function
# to measure eNMS performances when querying
# the database.
# flake8: noqa

from datetime import datetime

device_number = 200

factory_time = datetime.now()
for index in range(device_number):
    db.factory("device", name=str(index), commit=True)
print(f"'db.factory' time: {datetime.now() - factory_time}")

fetch_time = datetime.now()
for index in range(device_number):
    db.fetch("device", name=str(index))
print(f"'db.fetch' time: {datetime.now() - fetch_time}")

delete_time = datetime.now()
for index in range(device_number):
    db.delete("device", name=str(index))
    db.session.commit()
print(f"'db.delete' time: {datetime.now() - delete_time}")

print(f"Total duration: {datetime.now() - factory_time}")
