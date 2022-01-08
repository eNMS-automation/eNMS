# Create or Update an Instance
Used to create a new instance or modify an existing instance.

**Method:** PUT (update) or Post (create) <br />
**Address:** /rest/instance/`instance_type`<br/>
**Parameters:** None <br />
**Payload:** Pending

#
# Example

Schedule a task from the REST API: This payload will create the task `test`or
update if it already exists.
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
