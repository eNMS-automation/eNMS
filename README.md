<h1 align="center">eNMS</h1>
<h2 align="center">An enterprise-grade vendor-agnostic network automation platform.</h2>

# Introduction

eNMS is a vendor-agnostic NMS designed for building workflow-based network automation solutions.

[![eNMS](docs/source/_static/base/workflow.png)](https://www.demo.enms.io/workflow_builder)

It encompasses the following aspects of network automation:
  - **Configuration Management Service**: Backup with Git, change and rollback of configurations.
  - **Validation Services**: Validate data about the state of a device with Netmiko and NAPALM.
  - **Ansible Service**: Store and run Ansible playbooks.
  - **REST Service**: Send REST calls with variable URL and payload.
  - **Python Script Service**: Any python script can be integrated into the web UI. eNMS will automatically generate
a form in the UI for the script input parameters.
  - **Workflows**: Services can be combined together graphically in a workflow.
  - **Scheduling**: Services and workflows can be scheduled to start at a later time, or run periodically with CRON.
  - **Event-driven automation**: Services and workflows can be triggered from the REST API.

___

# Main features

## 1. Network creation

Your network topology can be created manually or imported from an
external Source of Truth (OpenNMS, LibreNMS, or Netbox).
Once created, it is displayed in a sortable and searchable table.
A dashboard provides a graphical overview of your network with dynamic charts.

Inventory                           |  Dashboard
:----------------------------------:|:-----------------------------------:
[![Inventory](docs/source/_static/base/inventory.png)](https://www.demo.enms.io/table/device) |  [![Dashboard](docs/source/_static/base/dashboard.png)](https://www.demo.enms.io/dashboard)

- Docs: _[Network Creation](https://enms.readthedocs.io/en/latest/inventory/network_creation/)_

## 2. Network visualization

eNMS can display your network on a world map (Google Map or Open Street Map).
Each device is displayed at its GPS coordinates.
Network topology diagrams can be created using devices and links from inventory, and adding labels for clarity.

Geographical View                |  Network Builder
:-------------------------------:|:-------------------------------:
[<img src="docs/source/_static/visualization/network_view.png" alt="Geographical View"/>](https://www.demo.enms.io/visualization/geographical_view) | [<img src="docs/source/_static/base/network_builder.png" alt="Network Builder"/>](https://www.demo.enms.io/visualization/logical_view)

- Docs: _[Network Visualization](https://enms.readthedocs.io/en/latest/inventory/network_visualization/)_

## 3. Service creation

eNMS comes with a number of "default services" leveraging libraries such as `ansible`, `requests`, `netmiko`, `napalm`  to perform simple automation tasks. However, absolutely any python script can be turned into a service. If your python script takes input parameters, eNMS will automatically generate a form in the web UI.

Services can be combined into a workflow.

[![Workflow Builder](docs/source/_static/base/workflow.png)](https://www.demo.enms.io/workflow_builder)

- Docs: _[Services](https://enms.readthedocs.io/en/latest/automation/services/)_, _[Workflow System](https://enms.readthedocs.io/en/latest/automation/workflows/)_

## 5. Configuration Management

eNMS can be used as a device configuration backup tool, like Oxidized/Rancid, with the following features:

  - Poll network devices and store the latest configuration in the database
  - Store any operational data that can be retrieved from the device CLI (e.g ``show version``, ``get facts`` etc.)
  - Search for any text or regular-expression in all configurations
  - Download device configuration to a local text file
  - Use the REST API support to return a specified device’s configuration
  - Export all configurations to a remote Git repository (e.g. Gitlab)
  - View git-style differences between various revisions of a configuration

Search Configuration                          |  Compare Configuration
:--------------------------------------------:|:-------------------------------:
[![Search](docs/source/_static/base/configuration_search.png)](https://www.demo.enms.io/table/configuration) |  [![History](docs/source/_static/base/configuration_history.png)](https://www.demo.enms.io/table/configuration)

- Docs: _[Configuration Management](https://enms.readthedocs.io/en/latest/inventory/configuration_management/)_

## 6. Event-driven automation

While services can be run directly and immediately from the UI, you can also schedule them to run at a later time, or periodically by defining a frequency or a CRON expression. All scheduled tasks are displayed in a calendar.

[![Calendar](docs/source/_static/base/calendar.png)](https://www.demo.enms.io/table/task)

Services can also be executed programmatically: eNMS has a REST API and a CLI interface that can be used to create, update and delete any type of objects, but also to trigger the execution of a service.

- Docs: _[Scheduling](https://enms.readthedocs.io/en/latest/automation/scheduling/)_

___


# Open Core vs Enterprise Edition

eNMS is available in two versions: an **Open Core** version (this repository), and an **Enterprise Edition** with advanced features for production deployments.

<div align="center">

| Feature | Open Core | Enterprise Edition |
|:-------:|:---------:|:------------------:|
| Workflow Automation | ✓ | ✓ |
| Configuration Management | ✓ | ✓ |
| Network Visualization | ✓ | ✓ |
| REST API | ✓ | ✓ |
| **Multi-User Authentication** | ✗ | ✓ |
| **Role-Based Access Control** | ✗ | ✓ |
| **Advanced Scheduler** | ✗ | ✓ |
| **TACACS+ / LDAP / Duo 2FA** | ✗ | ✓ |
| **Service Import / Export** | ✗ | ✓ |
| **Migration Mechanism** | ✗ | ✓ |
| **Change Revert / Audit Trail** | ✗ | ✓ |
| **Administration Panel** | ✗ | ✓ |
| **Production Scripts & Tools** | ✗ | ✓ |
| **Professional Support** | ✗ | ✓ |

</div>

## Enterprise Edition

The Enterprise Edition is ideal for organizations deploying eNMS in production environments where security, compliance, multi-tenancy, and professional support are critical requirements.

### Security & Authentication

- **Multi-User Authentication System**: Full login page with secure session management
- **Enterprise Authentication**: Support for TACACS+, LDAP, and Duo 2FA integration
- **Role-Based Access Control (RBAC)**: Configure granular permissions per user or group
  - Control who can view, edit, or run specific workflows and services (per user or per team)
  - Define access levels for devices, configurations, and network resources
- **User & Group Management**: Comprehensive administrative interface for managing teams and permissions

### Advanced Automation

- **Scheduler Application**: Advanced scheduling capabilities for workflow automation
  - Schedule with crontab expressions or specific date/time
  - Centralized view and control of scheduled tasks (with calendar interface)
- **Service Import / Export**: Package services and workflows as `.tgz` archives
  - Share automation solutions between different eNMS instances
  - Create backup archives of critical workflows
  - Transfer workflows between dev and production environments
- **Change Tracking & Revert**: Complete audit trail with rollback capability
  - Every modification is logged (who changed what and when)
  - One-click revert to any previous state

### Enterprise Administration

- **Administration Panel**: Centralized dashboard for system management
  - Server health monitoring and performance metrics
  - Worker process management and load balancing
- **Migration Mechanism**: Seamless backup and migration mechanism for upgrading between eNMS versions
  - Export / import your entire database in YAML or JSON format
  - Version-controlled migrations ensure data integrity during upgrades
- **Production Utilities**: Enterprise-grade maintenance scripts and tools
  - Database optimization and backup management
  - Advanced SQL debugging and log analysis

### Professional Support

- **Expert Technical Support**: Direct access to eNMS developers
- **Priority Bug Fixes**: Expedited resolution of critical issues
- **Implementation Assistance**: Help with deployment, customization, and best practices
- **Regular Updates**: Access to security patches and feature updates

**Interested in upgrading?** Visit [www.enms.io](https://www.enms.io) or contact us at [contact@enms.io](mailto:contact@enms.io) for pricing and licensing information.

___

# Architecture

[![eNMS System Overview](docs/source/_static/eNMS_overview.PNG)](https://enms.readthedocs.io/en/latest/)

___

# Quick Install
    Install python 3.12+ (earlier versions not supported)
    git clone https://github.com/afourmy/eNMS.git
    cd eNMS
    pip3 install -r build/requirements/requirements.txt
    export FLASK_APP=app.py
    flask run --host=0.0.0.0
    Log in (default credentials: admin / admin)
