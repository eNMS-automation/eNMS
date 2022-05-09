---
title: What is eNMS
---

## What is eNMS

eNMS is a vendor-agnostic Network Management System (NMS) designed for building
workflow-based network automation solutions.

![eNMS Introduction](./_static/base/workflow.png)

eNMS simplifies interaction with a wide variety of network device types for
automating complex operations like network audits or upgrades without 
worrying about the details of communication with each device.  eNMS developers
focus on the data not the communication.

For an overview, [see this diagram](#system-overview), below.

The following aspects of network automation are addressed:

- **Configuration Management Service**: Backup with Git, change and
    rollback of configurations.
- **Validation Services**: Validate data about the state of a device
    with Netmiko, NETCONF, NAPALM, or Scrapli.
- **Ansible Service**: Store and run Ansible playbooks.
- **REST Service**: Send REST calls with variable URL and payload.
- **Python Script Service**: Any python script can be integrated
    into the web UI. eNMS will automatically generate a form in the UI
    for the script input parameters.
- **Workflows**: Services can be combined graphically in a workflow.
- **Scheduling**: Services and workflows can be scheduled to start
    at a later time, or run periodically with CRON, as well as run on
    demand.
- **Event-driven automation**: Services and workflows can be
    triggered from the REST API.

## System Overview

![eNMS System Overview](./_static/eNMS_overview.PNG)

