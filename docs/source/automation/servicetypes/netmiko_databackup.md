This service uses Netmiko CLI commands to retrieve and store information from
devices.

![Netmiko Data Backup Service](../../_static/automation/builtin_service_types/netmiko_databackup.png)

## Target Property and Commands

-   Property to update (e.g `Configuration`)
-   `Commands` - This is a series of twelve commands that are used to
    pull data from the device.
-   `Label` This is the label the data will be given in the results

## Search Response and Replace

![Netmiko Data Backup Parameters](../../_static/automation/builtin_service_types/netmiko_searchresponsereplace.png)

-   Used to filter out unwanted information
-   `Pattern` The pattern to search through the retrieved data to
    replace
-   `Replace With` This is what will be substituted when the `pattern`
    is found.
