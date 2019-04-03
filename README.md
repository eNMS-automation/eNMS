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

[![eNMS](docs/_static/base/enms.png)](http://afourmy.pythonanywhere.com/views/geographical_view)

It encompasses the following aspects of network automation:
- **Configuration Management Service**: Commit / Rollback of a configuration with Napalm or Netmiko.
- **Ansible Service**: Sending and managing Ansible playbooks.
- **ReST Service**: Sending a ReST call (GET/POST/UPDATE/DELETE) with variable URL and payload.
- **Custom Services**: Any python script can be integrated into the web UI. If the script takes input parameters, a form will be automatically generated.
- **Workflows**: Services can be combined together graphically in a workflow.
- **Scheduling**: Services and workflows can be scheduled to start at a later time, or run periodically.
- **Event-driven automation**: Services and workflows can be triggered by an external event (ReST call or Syslog message).

[![Workflow System](docs/_static/base/workflow.gif)](http://afourmy.pythonanywhere.com/automation/workflow_builder/)

___

# Main features

## 1. Network creation

Devices and links can be created either one by one, or all at once by importing an Excel spreadsheet.

Once created, all objects are displayed in a sortable and searchable table, from which they can be edited and deleted.

A dashboard provides a graphical overview of all objects with dynamic charts.

Inventory                           |  Dashboard
:----------------------------------:|:-----------------------------------:
[![Inventory](docs/_static/base/inventory.png)](http://afourmy.pythonanywhere.com/objects/device_management) |  [![Dashboard](docs/_static/base/dashboard.png)](http://afourmy.pythonanywhere.com/dashboard)

- Online demo: _[Dashboard](http://afourmy.pythonanywhere.com/dashboard)_, _[Inventory](http://afourmy.pythonanywhere.com/objects/device_management)_
- Docs: _[Objects](https://enms.readthedocs.io/en/latest/inventory/objects.html)_

## 2. Network visualization

Once created, eNMS can display your network:
- geographically on a 2D or 3D world map (with the tile layer of your choice: Open Street Map, Google Map...)
- logically with a force-based algorithm (`d3.js`).

You can click on a device to display its properties or start a Web SSH terminal session.

Geographical View                             |  Logical View
:--------------------------------------------:|:-------------------------------:
[![Geographical](docs/_static/base/enms.png)](http://afourmy.pythonanywhere.com/views/geographical_view) |  [![Logical](docs/_static/base/logical_view.png)](http://afourmy.pythonanywhere.com/views/logical_view)

- Online demo: _[Geographical View](http://afourmy.pythonanywhere.com/views/geographical_view)_, _[Logical View](http://afourmy.pythonanywhere.com/views/logical_view)_
- Docs: _[Geographical View](https://enms.readthedocs.io/en/latest/views/geographical_view.html)_, _[Logical View](https://enms.readthedocs.io/en/latest/views/logical_view.html)_

## 3. Service creation

eNMS comes with a number of "default services" leveraging libraries such as `ansible`, `requests`, `netmiko`, `napalm`  to perform simple automation tasks. However, absolutely any python script can be turned into a "service".
If your python script takes input parameters, eNMS will automatically generate a form in the web UI.

To generate a form that matches your service, eNMS will perform the following conversion:
- python `string` -> Text box (single line or multiline)
- python `list` -> Drop-down list (single or multiselect).
- python `bool` -> Checkbox.
- python `dict` -> Text box expecting a dictionary.

![eNMS](docs/_static/base/form_generation.png)

Once created, you can have as many instances of your service as you need. Service instances can be executed, edited and deleted from the web UI.

[![Service Management](docs/_static/base/service_management.png)](http://afourmy.pythonanywhere.com/automation/service_management)

- Online demo: _[Services](http://afourmy.pythonanywhere.com/automation/service_management)_
- Docs: _[Services](https://enms.readthedocs.io/en/latest/services/service_system.html)_, _[Default Services](https://enms.readthedocs.io/en/latest/services/default_services.html)_

## 4. Workflows

Services (and other Workflows) can be combined into a single workflow.

Within a workflow, services can be connected with two edge types: `Success` edge and `Failure` edge. The `Success` edge (versus `Failure` edge) indicates which path to follow in the graph if the source service is successfully executed (versus failed).

A workflow keeps track of a `payload` dictionary, such that when a service starts, it has access to the results of all previously executed services.

When a workflow is executed, its status will be updated in real-time on the web UI.

[![Workflow Builder](docs/_static/base/workflow.png)](http://afourmy.pythonanywhere.com/automation/workflow_builder/)

- Online demo: _[Workflow Builder](http://afourmy.pythonanywhere.com/automation/workflow_builder/)_
- Docs: _[Workflow System](https://enms.readthedocs.io/en/latest/workflows/workflow_system.html)_, _[Workflow Payload](https://enms.readthedocs.io/en/latest/workflows/workflow_payload.html)_

## 5. Scheduling

While services and workflows can be run directly and immediately from the web UI, you can also schedule them to run at a later time, or periodically by defining a frequency, a start date and an end date. All scheduled tasks are displayed in a calendar.

[![Calendar](docs/_static/base/calendar.png)](http://afourmy.pythonanywhere.com/scheduling/calendar)

- Online Demo: _[Calendar](http://afourmy.pythonanywhere.com/scheduling/calendar)_
- Docs: _[Scheduling](https://enms.readthedocs.io/en/latest/scheduling/task_management.html)_

## 6. Configuration Management

eNMS can work as a network device configuration backup tool and replace Oxidized/Rancid with the following features:
- Poll network elements; download configurations when they change
- Easily view the current configuration of a device in the inventory
- Search for any text in any configuration
- View differences between various revisions of a configuration
- Download device configuration to a local text file
- Use the ReST API support to return a specified device’s configuration
- Export all device configurations to a remote Git repository (e.g. Gitlab)

[![Configuration Management](docs/_static/base/configuration_management.png)](http://afourmy.pythonanywhere.com/scheduling/calendar)

## 6. Event-driven automation

Event-driven automation in eNMS has two aspects:
- eNMS has a ReST API that can be used to create, update and delete any type of objects (services, workflows, tasks), but also to trigger the execution of a service or a workflow with a GET request to the appropriate URL. 
- eNMS can be configured as a Syslog server: all logs are stored in the database, and rules can be created to trigger the execution of a service or a workflow upon receiving a log matched by the rule.

Docs: _[ReST API](https://enms.readthedocs.io/en/latest/event_driven/rest_api.html)_

## Notification system

After a service or a workflow is executed, you can configure eNMS to send a notification with the results.
Three types of notification are available:
- via mail (a brief summary and the full logs attached as a textfile)
- via Slack
- via Mattermost (Open-Source and private alternative to Slack)

Additionally, eNMS can be configured to push the results to a remote Git repository.

___

# Advanced features

## 1. Authentication

- eNMS supports TACACS+ and LDAP/Active Directory authentication: upon logging in, a request will be sent to your TACACS+/LDAP server to validate the credentials and log in the user.
- Authentication with RADIUS is currently under development.

## 2. Network creation with external Network Source of Truth

If you use an NSoT like OpenNMS or Netbox to document your network, eNMS can automatically import the network topology (devices and links), as well as all IP addresses and geographical coordinates.

## 3. Network export

- Networks can be exported as an Excel file. 
- Networks can be exported as a `kmz` file for you to visualize your network on Google Earth.

___

# Getting started

## Quick start
    Install python 3.6+ (earlier versions not supported)
    git clone https://github.com/afourmy/eNMS.git
    cd eNMS
    pip3 install -r requirements.txt
    export FLASK_APP=app.py (on Windows, use `set` instead of `export`)
    flask run --host=0.0.0.0
    Log in (default credentials: admin / admin)

## Quick start as a docker container
    docker run -d -p 5000:5000 --name enms --restart always afourmy/enms
    Log in (default credentials: admin / admin)

## Deploy eNMS in production

In production, eNMS is configured to use a PostgreSQL database and a Hashicorp Vault (storage of network credentials).

Check out the `Installation` section of the docs: _[Install eNMS](https://enms.readthedocs.io/en/latest/base/installation.html)_

# Contact

For any feedback, advice, feature request, join us on the [Network to Code slack](http://networktocode.herokuapp.com "Network to Code slack"), channel **#enms**.

___

# Coming up next

- RADIUS authentication
- Database clustering architecture
- Training Videos

# Other projects you might be interested in

- _[Flask Gentelella](https://github.com/afourmy/flask-gentelella)_: The Flask/Bootstrap template eNMS is built upon.
- _[pyNMS](https://github.com/afourmy/pyNMS)_: A PyQt software for network simulation and optimization.
- _[SWAP](https://github.com/afourmy/SWAP)_: A solver for the Wavelength Assignment Problem in optical networks.