# Service Types

eNMS provides a rich suite of Service Types for managing and interacting 
with network equipment. 

## Ansible Playbook Service

- [Ansible Playbook Service](servicetypes/ansible_playbook.md) runs an ansible
  playbook on a set of target devices and returns a JSON formatted result.

## Data Processing Service

Process some data from the payload with a python query, and optionally
post-process the result with a regular expression, TextFSM template, Jinja2
Template, or TTP Template:

- [Data Processing Service](servicetypes/data_processing.md).

## Data Validation Service

Extract some data from the payload, and validate it against a string or
a dictionary. This is used for conducting extra validations, of a prior
service's result, later in a workflow:

- [Data Validation Service](servicetypes/data_validation.md).

## Generic File Transfer Service

Transfer a single file to/from the eNMS server to the device using
either SFTP or SCP:

- [Generic File Transfer Service](servicetypes/generic_filetransfer.md).

## GIT Action Service

Perform a GIT action on a set of files used or created by a workflow:

- [GIT Action Service](servicetypes/git_action.md).

## ICMP / TCP Ping Service

Implements a Ping from this automation server to the selected devices
from inventory using either ICMP or TCP:

- [ICMP / TCP Ping Service](servicetypes/icmptcp_ping.md).

## Mail Notification Service

This service is used to send an automatically generated email to a list
of recipients:

- [Mail Notification Service](servicetypes/mail_notification.md).

## Mattermost Notification Service

This service will send a message to a mattermost server that is
configured in the eNMS settings:

- [Mattermost Notification Service](servicetypes/mattermost_notification.md).

## Napalm Services

Napalm connections are SSH connections to equipment in which a
pre-defined set of data is retrieved from the equipment and presented to
the user in a structured (dictionary) format. The following are the common
parameters for all Napalm services:

- [Napalm Common Parameters](servicetypes/napalm_common.md).

And the specifics for each Napalm service are in their own sections:

- [Napalm Data Backup Service](servicetypes/napalm_databackup.md).
- [Napalm Configuration Service](servicetypes/napalm_configuration.md).
- [Napalm Getters Service](servicetypes/napalm_getters.md).
- [Napalm Ping Service](servicetypes/napalm_ping.md).
- [Napalm Rollback Service](servicetypes/napalm_rollback.md).
- [Napalm Traceroute Service](servicetypes/napalm_traceroute.md).

## Netconf (ncclient) Service

Send an XML payload to a device netconf interface:

- [Netconf (ncclient) Service](servicetypes/netconf_ncclient.md).

## Netmiko Services

The Netmiko services provide the ability to perform multiple CLI actions
through an SSH connection. The following are the values common to every
Netmiko service:

- [Netmiko Common Parameters](servicetypes/netmiko_common.md).

And the specifics for each Netmiko service are in their own sections:

- [Netmiko Data Backup Service](servicetypes/netmiko_databackup.md).
- [Netmiko Commands Service](servicetypes/netmiko_commands.md).
- [Netmiko Configuration Service](servicetypes/netmiko_configuration.md).
- [Netmiko File Transfer Service](servicetypes/netmiko_filetransfer.md).
- [Netmiko Prompts Service](servicetypes/netmiko_prompts.md).

## Python Snippet Service

Runs any python code:

- [Python Snippet Service](servicetypes/python_snippet.md).

## REST Call Service

Send a REST call (GET, POST, PUT or DELETE) to a URL with optional
payload. The output can be validated with a command / pattern mechanism,
like the `Netmiko Commands Service`:

- [REST Call Service](servicetypes/rest_call.md).

## Scrapli Services
 
The Netmiko services provide the ability to perform multiple CLI actions
through an SSH connection. The following are the values common to every
Netmiko service:

- [Scrapli Common Parameters](servicetypes/scrapli_common.md).

And the specifics for each Scrapli service are in their own sections:

- [Scrapli Commands Service](servicetypes/scrapli_command.md).
- [Scrapli Data Backup Service](servicetypes/scrapli_databackup.md).

## Scrapli Netconf Service

Send an XML payload to a device netconf interface using Scrapli:

- [Scrapli Netconf Service](servicetypes/scrapli_netconf.md).

## Slack Notification Service

This service will send a message to the slack server that is configured
in the eNMS settings:

- [Slack Notification Service](servicetypes/slack_notification.md).

## Topology Import Service

Import the network topology from an instance of LibreNMS, Netbox or OpenNMS:

- [Topology Import Service](servicetypes/topology_import.md).

## UNIX Command Service

Runs a UNIX command **on the server where eNMS is installed**:

- [Unix Command Service](servicetypes/unix_command.md).

## UNIX Shell Service

Runs a BASH script on a target device:

- [Unix Shell Service](servicetypes/unix_shell.md).

## Workflow (Subworkflow) Service

Create a subworkflow service and add to the current workflow in Workflow
Builder:

- [Subworkflow Service](servicetypes/workflow.md).
