# Uses eNMS fetch, factory and delete function
# to measure eNMS performances when querying
# the database.

from datetime import datetime

device_number = 200
start_time = datetime.now()

for index in range(device_number):
    db.factory("device", name=str(index), commit=True)

for index in range(device_number):
    db.fetch("device", name=str(index))

for index in range(device_number):
    db.delete("device", name=str(index))
    db.session.commit()

end_time = datetime.now()

print(f"Total duration: {end_time - start_time}")
