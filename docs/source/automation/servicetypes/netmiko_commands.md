Uses Netmiko to send a command to a device to
determine the state of that device. See the `Workflow` section for
examples of how it is used in a workflow.

![Netmiko Validation Service](../../_static/automation/service_types/netmiko_commands.png)

Each command is sent to the device and the output is saved as the
service result.  eNMS collects output from each command until
either the prompt or the `expect string` is matched in the output, or until
the `timeout` has elapsed.

While output processing is simpler when a single command is specified,
the service supports sending multiple commands as a single service.  The
same configuration parameters are used for Each command.

By default, the output from all commands is returned as a single string.
When multiple commands are specified, a header is prepended to the output
to help identify what output is from which command.  Results from each command can also be returned as a list, using the
`Results As List` option. 

Configuration parameters for creating this service instance:

-  All [Netmiko Service Common Parameters](netmiko_common.md).

- `Commands`: Command(s) to be sent to the device, with each command on a separate line.

- `Results as List` - If checked, store the command output as a list of 
   individual string results. By default, all output is returned as a single string,
   with a COMMAND header prepended multiple commands are specified.

Also included in Netmiko Advanced Parameters: 

![Netmiko Configuration Advanced Parameters](../../_static/automation/service_types/netmiko_validation_advanced.png)

- `Use TextFSM`- Causes Netmiko to try and match the command to a TextFSM
  template pointed to in the system by the `NET_TEXTFSM` environment
  variable. The Network to Code project maintains a repository of TextFSM
  templates for popular network devices [here](https://github.com/networktocode/ntc-templates).
- `Auto Find Prompt` - Tries to detect the prompt automatically. Mutually exclusive with `Expect String`.
- `Expect String` - Regular expression that signifies the end of output.
- `Config Mode Command` - The command that will be used to enter config
  mode.
- `Strip command` - Remove the echo of the command from the output
  (default: True).
- `Strip prompt`- Remove the trailing router prompt from the output
  (default: True).

!!! note

    `Expect String` and `Auto Find Prompt` are mutually exclusive; both
    cannot be enabled at the same time. If the user does not expect Netmiko
    to find the prompt automatically, the user should provide the expected
    prompt instead. This is useful when the CLI command sent via Netmiko
    causes the prompt to change, or when restarting and no prompt is expected.
!!! note

    This service supports variable substitution in some input fields of its
    configuration form.
