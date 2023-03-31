# Configuration Management

## Overview 

eNMS can be used as a device configuration backup utility, like Oxidized/RANCID,
with the following features:

-   Poll network devices and store the latest configuration in the
    database.
-   Store any operational data that can be retrieved from the device
    CLI (e.g `show version`, `show platform` etc.).
-   Search for any text or regular-expression in all configurations.
-   Download device configuration to a local text file.
-   Use the REST API support to return a specified device's
    configuration.
-   Export all configurations to a remote Git repository (e.g. Gitlab).
-   View git-style differences between various revisions of a
    configuration.

## Search and display the configuration

From the `Inventory -> Configurations` tab, the user can search for a specific 
word, a string that is included in a pattern or a regular expression in 
the current configuration of all devices, using the *Configuration*
column. eNMS will filter the list of devices based on whether the
current configuration of the device contains the search criteria. Select
the "Lines of Context" slider at the top of the UI to see up to 5
lines, before and after the specified word that was searched.

### Viewing configuration 

Click on the `Network Data` button on the right of the screen to
display the device Configuration (or select Operational Data).

![Configuration Search.](../_static/base/configuration_search.png)

### Historical comparison 

Click on the `Historic` button on the right of the screen to
view the differences between various revisions of the device
configuration.

![Configuration Comparison.](../_static/base/configuration_history.png)

## Data Backup Services - Overview 

Configurations are retrieved by `Data Backup` services which:

- Fetch the device configuration or operational data (or other configuration property) 
  using Netmiko, NAPALM, or Scrapli. 
- Updates the device `Configuration`, `Operational Data`, or `Specialized
  Data` property, depending on which one is selected in the service.

For some devices, the configuration cannot be retrieved with only a
single Netmiko command. In this case, one can either use:

- the `NAPALM Data Backup` Service to substitute a napalm getter, such as get_config, in
place of retrieving the configuration via a single CLI command.
- the `Scrapli Data Backup` Service with multiple commands.

Please refer to [Services Types](../../automation/service_types/) for more 
information about the specifics of each Data Backup service.

### Custom Data Backup Services 

As an alternative to the existing `Data Backup` Services, one can create a custom 
configuration backup service(s) if required. See [Customization ](
../../advanced/customization/#custom-service-types) for more information.

### Additional configuration properties

Additional configuration-style properties can be defined in the `setup/properties.json`.
Defining extra *configuration* properties allows the Data Backup services (e.g., Netmiko, 
NAPALM, Scrapli) to be able to collect and store additional data sets.


## Collecting and Updating Configuration Data 

### Pull configurations from git

Collected configurations and operational data are written to local text 
files, located in `network_data/`, which are mapped in the `settings.json` to a git
repository.

Git is used for storing historical revisions of the data, and each additional
instance of eNMS can retrieve the Git history using the
`Admin Button -> Fetch Git Configurations Button`. Git fetch can also be
configured in cron to periodically get triggered through the CLI to
update the Configurations that were pushed into Git by another instance
of eNMS.

!!! note
 
    Each of the `Data Backup` services has an option, `Local Path`, that provides the 
    ability to store text files in a directory other than `network_data`.

### Updating configurations 

Upon retrieving the current configuration from a device using a `Data Backup` Service, 
the config is added to the database, as well to the local text file. 

After data is collected and updated, this data can be pushed from the local Git 
repository folder to a remote (if one is configured).  

!!! attention

    Multiple instances of eNMS pushing to the same `network_data/` repository
    may result in merge conflicts on some or all instances which will halt
    further updates. 

    To prevent this, the user can install a custom merge driver in the
    `network_data/` repo that allows git to automatically merge based on the
    most recent commit, as detailed in the [Installation docs](../base/installation.md#network-data-merge-driver).
    
### Git command support 

The [Git Action Service](../../automation/servicetypes/git_action/) provides support 
for running Git commands (pull, push, etc.) inside a Workflow.  A typical configuration 
collection Workflow will include `Git Action` services as well as `Data Backup`
services.


