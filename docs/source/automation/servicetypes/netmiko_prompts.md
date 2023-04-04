Similar to Netmiko Commands Service, but expects up to 3 interactive
prompts for your remote command, such as 'Are you sure? Y/N'. This
service allows the user to specify the expected prompt and response to
send to the device for it.

![Netmiko Prompts Service](../../_static/automation/service_types/netmiko_prompts.png)

Configuration parameters for creating this service instance:

- All [Netmiko Service Common Parameters](netmiko_common.md).
-   `Command` - CLI command to send to the device.
-   `Confirmation1` - Regular expression to match the first expected
    confirmation question prompted by the device.
-   `Response1` - Response to the first confirmation question prompted by the
    device.
-   `Confirmation2` - Regular expression to match the second expected
    confirmation question prompted by the device.
-   `Response2` - Response to the second confirmation question prompted by the
    device.
-   `Confirmation3` - Regular expression to match the third expected
    confirmation question prompted by the device.
-   `Response3` - Response to the third confirmation question prompted by the
    device.

!!! note

    This service supports variable substitution in all input fields of its
    configuration form.
