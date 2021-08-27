# Functions provided by eNMS
# flake8: noqa

# Factory: create a new instance

device = db.factory("device", name="test", model="IOS", commit=True)
print(f"Device '{device}' has been created")

# Fetch: retrieve instance from database

device = db.fetch("device", name="test")
print(f"Device '{device}' retrieved from database")

# Factory: edit existing instance
# We use factory to update the "model" property of Washington

print(f"Old model: {device.model}")
device = db.factory("device", name="test", model="EOS")
print(f"New model: {device.model}")

# Delete: erase instance from database

db.delete("device", name="test")
db.session.commit()

get_deleted_device = db.fetch("device", name="test", allow_none=True)

if get_deleted_device is None:
    print("Device has been deleted")
