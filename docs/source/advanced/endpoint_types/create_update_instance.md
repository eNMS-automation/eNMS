# Create or Update an Instance
Used to create a new instance or modify an existing instance.

**Method:** POST (update or create) <br />
**Address:** /rest/instance/`instance_type` <br />
**Parameters:** None <br />
**Payload:** JSON representation of the dictionary data needed to create the 
  object instance and depends on the object type <br />

!!! Note
     An object can be renamed by setting the `name` key to the current name,
     and the `new_name` key to the new name.

# Examples

## Disable (prevent execution) of a workflow.

POST /rest/instance/service
```json
{
    "name": "Device Iteration",
    "disabled": true
}
```

## Schedule a task from the REST API: This payload will create the task `test` or update it if it already exists.

POST /rest/instance/task
```json
{
  "name": "test",
  "service": "netmiko_check_vrf_test",
  "is_active": true,
  "devices": ["Baltimore"],
  "start_date": "13/08/2019 10:16:50"
}
```
!!! Note
     This task schedules the service `netmiko_check_vrf_test` to run at
    `20/06/2019 23:15:15` on the device whose name is `Baltimore`.

## Update a device called DALLAS and change its IP address:

POST /rest/instance/device
```json
{
  "name": "DALLAS",
  "ip_address": "10.1.1.1",
}
```

