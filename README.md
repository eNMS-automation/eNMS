<h1 align="center">eNMS</h1>
<h2 align="center">An enterprise-grade vendor-agnostic network automation platform.</h2>

___

<table>
    <thead>
        <tr>
            <th>Branch</th>
            <th>Status</th>
            <th>Coverage</th>
            <th>Documentation</th>
            <th>Python Style</th>
            <th>JavaScript Style</th>
            <th>License</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>master</td>
            <td><a href="https://travis-ci.org/afourmy/eNMS"><img src="https://travis-ci.org/afourmy/eNMS.svg?branch=master" alt="Build Status (master branch)"></img></a></td>
            <td><a href="https://coveralls.io/github/afourmy/eNMS?branch=master"><img src="https://coveralls.io/repos/github/afourmy/eNMS/badge.svg?branch=master" alt="Coverage (master branch)"></img></a></td>
            <td><a href="https://enms.readthedocs.io/en/latest/?badge=master"><img src="https://readthedocs.org/projects/enms/badge/?version=stable" alt="Documentation (master branch)"></img></a></td>
          <td rowspan=2><img alt="PEP8" src="https://img.shields.io/badge/code%20style-pep8-orange.svg"><br><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></td>
          <td rowspan=2><img alt="Code style: google" src="https://img.shields.io/badge/code%20style-google-blueviolet.svg"><br><img alt="Code style: prettier" src="https://img.shields.io/badge/code_style-prettier-ff69b4.svg"></td>
          <td rowspan=2><a href="https://www.gnu.org/licenses/gpl-3.0"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="License"></img></a></td>
        </tr>
        <tr>
            <td>develop</td>
            <td><a href="https://travis-ci.org/afourmy/eNMS"><img src="https://travis-ci.org/afourmy/eNMS.svg?branch=develop" alt="Build Status (develop branch)"></img></a></td>
            <td><a href="https://coveralls.io/github/afourmy/eNMS?branch=develop"><img src="https://coveralls.io/repos/github/afourmy/eNMS/badge.svg?branch=develop" alt="Coverage (develop branch)"></img></a></td>
            <td><a href="https://enms.readthedocs.io/en/latest/?badge=develop"><img src="https://readthedocs.org/projects/enms/badge/?version=develop" alt="Documentation (develop branch)"></img></a></td>
        </tr>
    </tbody>
</table>

___

# Introduction

eNMS is a vendor-agnostic NMS designed for building workflow-based network automation solutions.

[![eNMS](docs/_static/enms.png)](http://afourmy.pythonanywhere.com/views/geographical_view)

It encompasses the following aspects of network automation:
  - **Configuration Management Service**: Backup with Git, change and rollback of configurations.
  - **Validation Services**: Validate data about the state of a device with Netmiko and NAPALM.
  - **Ansible Service**: Store and run Ansible playbooks.
  - **REST Service**: Send REST calls with variable URL and payload.
  - **Python Script Service**: Any python script can be integrated into the web UI. eNMS will automatically generate
a form in the UI for the script input parameters.
  - **Workflows**: Services can be combined together graphically in a workflow.
  - **Scheduling**: Services and workflows can be scheduled to start at a later time, or run periodically with CRON.
  - **Event-driven automation**: Services and workflows can be triggered by an external event (REST call, Syslog message, etc).

___

# Main features

## 1. Network creation

Your network topology can be created manually or imported from an
external Source of Truth (OpenNMS, LibreNMS, or Netbox).
Once created, it is displayed in a sortable and searchable table.
A dashboard provides a graphical overview of your network with dynamic charts.

Inventory                           |  Dashboard
:----------------------------------:|:-----------------------------------:
[![Inventory](docs/_static/base/features/inventory.png)](https://enms.readthedocs.io/en/develop/inventory/network_creation.html) |  [![Dashboard](docs/_static/base/features/dashboard.png)](https://enms.readthedocs.io/en/develop/inventory/network_creation.html)

- Docs: _[Objects](https://enms.readthedocs.io/en/develop/inventory/network_creation.html)_

## 2. Network visualization

eNMS can display your network on a world map (Google Map or Open Street Map).
Each device is displayed at its GPS coordinates.
You can click on a device to display its properties, configuration, or start an SSH terminal session.
Colocated devices can be grouped into geographical sites (campus, dacacenter, ...),
and displayed logically with a force-directed layout.

Network View                                  |  Sites View
:--------------------------------------------:|:-------------------------------:
[![Geographical](docs/_static/inventory/network_visualization/network_view.png)](https://enms.readthedocs.io/en/develop/inventory/network_visualization.html) |  [![Logical](docs/_static/inventory/network_visualization/site_view.png)](https://enms.readthedocs.io/en/develop/inventory/network_visualization.html)

- Docs: _[Geographical View](https://enms.readthedocs.io/en/develop/inventory/network_visualization.html)_

## 3. Service creation

eNMS comes with a number of "default services" leveraging libraries such as `ansible`, `requests`, `netmiko`, `napalm`  to perform simple automation tasks. However, absolutely any python script can be turned into a service. If your python script takes input parameters, eNMS will automatically generate a form in the web UI.

Services can be combined into a workflow.

[![Workflow Builder](docs/_static/base/features/workflow.png)](https://enms.readthedocs.io/en/develop/automation/workflows.html)

- Docs: _[Workflow System](https://enms.readthedocs.io/en/develop/automation/workflows.html)_, _[Workflow Payload](https://enms.readthedocs.io/en/latest/workflows/workflow_payload.html)_

## 5. Event-driven automation

While services can be run directly and immediately from the web UI,
you can also schedule them to run at a later time, or periodically by defining a frequency,
a start date and an end date. All scheduled tasks are displayed in a calendar.

[![Calendar](docs/_static/base/features/calendar.png)](https://enms.readthedocs.io/en/develop/automation/execution.html)

Services can also be executed programmatically:
  - eNMS has a REST API and a CLI interface that can be used to create, update and delete any type of objects,
    but also to trigger the execution of a service.
  - eNMS can be configured as a Syslog server, and rules can be created for syslog messages
    to trigger the execution of a service.

- Docs: _[Scheduling](https://enms.readthedocs.io/en/develop/automation/execution.html)_, _[REST API](https://enms.readthedocs.io/en/develop/advanced/rest_api.html)_

## 6. Configuration Management

eNMS can work as a network device configuration backup tool and replace
Oxidized/Rancid with the following features:

  - Poll network elements and store the latest configuration in the database
  - Search for any text or regular-expression in all configurations
  - Download device configuration to a local text file
  - Use the REST API support to return a specified device’s configuration
  - Export all configurations to a remote Git repository (e.g. Gitlab) to view differences between various revisions of a configuration

___

# Getting started

## Online content

- An _[overview of eNMS](https://www.youtube.com/watch?v=XwU0yom_aY0&t=1205s)_ on youtube
- A _[podcast about eNMS and network automation](https://www.pythonpodcast.com/enms-network-automation-episode-232/)_

## Quick Installation
    Install python 3.6+ (earlier versions not supported)
    git clone https://github.com/afourmy/eNMS.git
    cd eNMS
    pip3 install -r requirements.txt
    export FLASK_APP=app.py
    flask run --host=0.0.0.0
    Log in (default credentials: admin / admin)

## Contact

For any feedback, advice, feature request, join us on the [Network to Code slack](http://networktocode.herokuapp.com "Network to Code slack"), channel **#enms**.
