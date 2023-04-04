This service uses Napalm to pull data from devices and store it in
`Inventory -> Configuration` for later comparison and for historical tracking.

![Napalm Data Backup Service](../../_static/automation/service_types/napalm_databackup.png)


## Configuration parameters for creating this service instance:

- All [Napalm Service Common Parameters](napalm_common.md) 

- `Configuratioon Property to Update` - Choose the target property to backup.
- `Local Path` - Specify the path of the file to store the backup data (the path is relative to the ien-ap directory.
- `Getters` - Choose the configuration getters to be used to back up the target property.

!!! note
 
    This service can be used to store other Napalm Getter's data into the
    Operational Data field for a device.
    
## Search Response & Replace

These fields allow a `Pattern` in the collected data to be `Replaced With` 
some other data. This can be used to remove frequently changing data from 
device output, such as timestamps or dates. It can also be used to remove
sensitive data from the device output, such as passwords.
