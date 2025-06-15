The UNIX Command Service allows for a command to be issued on this eNMS
server instance. This is useful for transferring or setting file
permissions prior to using a file in a workflow.

![UNIX Command Service](../../_static/automation/service_types/unix_command.png)

Configuration parameters for creating this service instance: 

- `Command`: UNIX command to run on the server.
- `Approved by an Admin user`: A Unix Command service can only be run if this box
  is checked. Whenever a Unix Command service is edited or duplicated by a non-admin user,
  it must be re-approved.

!!! note

    When a non-admin user edits via the edit panel, the "Approved by admin" checkbox
    must be unchecked to validate the form. When a Unix Command service is deep-copied
    into a workflow, that property will be automatically unchecked.

!!! note

    This service supports variable substitution of input fields 
    of its configuration form.
