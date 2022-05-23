The Scrapli Commands service works similar to Netmiko Commands; but it allows
one or multiple commands to be sent to the device via Scrapli library, and
it allows for the validation of the returned result.

![Scrapli Command Service](../../_static/automation/builtin_service_types/scrapli.png)

Scrapli Project Documentation can be reviewed
[HERE](https://carlmontanari.github.io/scrapli/user_guide/project_details/)

## Common Parameters

- All [Scrapli Common Parameters](scrapli_common.md).


## Main Parameters

- `Commands`: Commands to be send to the device, each command on a separate line.

- `Results as List`: if checked, store the results of the commands as a list of 
   individual string results. If not checked, this is a single string.
    
