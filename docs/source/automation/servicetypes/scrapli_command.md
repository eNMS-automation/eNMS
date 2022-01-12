Scrapli command service works similar to Netmiko Validation; but it allows
one or multiple commands to be sent to the device via Scrapli library, and
it allows for the validation of the returned result.

![Scrapli Command Service](../../_static/automation/builtin_service_types/scrapli.png)

Scrapli Project Documentation can be reviewed
[HERE](https://carlmontanari.github.io/scrapli/user_guide/project_details/)

## Main Parameters

- `Commands`: Commands to be send to the device
- `Is Configuration`:  Should the device be put in config mode before
  issuing the commands?
- `Driver`: Scrapli driver to use. Currently, it supports:
    
    - `arista_eos`
    - `cisco_iosxe`
    - `cisco_iosxr`
    - `cisco_nxos`
    - `juniper_junos`
    
- `Transport`: Supports using the following transport plugins:

    - `system`: Wrapper around OpenSSH/System available SSH binary
    - `paramiko`: Wrapper around paramiko library
    - `ssh2`: Wrapper around ssh2-python library
    
## Connection Parameters

- `Credentials`: Select between:
    - `Device Credentials` - eNMS will select the most appropriate credential
      object for each device. If there are multiple credentials available, eNMS
      will use the `Type of Credential` and `Priority` properties as a tie
      breaker.
    - `User Credentials` - Use the user's currently logged in credentials to
      access the device.
    - `Custom Credentials` - The user provides the credentials below:

- `Custom Username` - User provided username

- `Custom Password` - User provided password

- `Start New Connection`: **Before the service runs**, the current
  cached connection is discarded and a new one is started.
    
- `Connection Name`: If changed to something other than `default`, the
  connection will be cached as a separate connection to that same device.
  This allows for multiple simultaneous "named" connections to a single
  device, as in this example:
    
- `Close Connection`: Once the service is done running, the current
  connection will be closed.
