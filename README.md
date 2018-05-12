[![Build Status](https://travis-ci.org/afourmy/eNMS.png)](https://travis-ci.org/afourmy/eNMS)
[![Coverage Status](https://coveralls.io/repos/github/afourmy/eNMS/badge.svg?branch=master)](https://coveralls.io/github/afourmy/eNMS?branch=master)

# Introduction

eNMS is an open source web application designed to help automate networks graphically.

![eNMS](readme/eNMS.png)

It encompasses the following aspects of network automation:
- **Configuration management**: commit/rollback of a configuration via NAPALM.
- **Netmiko scripting**: using netmiko to push a configuration, or display the result of a set of commands.
- **Ansible support**: sending and managing ansible playbooks.
- **Scheduling**: any task can be scheduled to run at a specific time, periodically or not.

While network automation traditionally requires scripting skills, eNMS provides a way to automate networks graphically, in a few simple steps: 
- **Creation** of the network (e.g by importing a spreadsheet describing the network topology)
- **Visualization** of the network on a world map, or via a force-based algorithm.
- **Selection** of the target devices, on the graphical view.
- **Scheduling** of the script.

Join us on the [Network to Code slack](http://networktocode.herokuapp.com "Network to Code slack"), channel #enms for the latest updates !

# 1. Network creation

Nodes and links can be created either one by one by specifying all properties manually, or all at once by importing an Excel spreadsheet. Once created, all objects are displayed in a sortable and searchable table, from which they can be edited and deleted.
The dashboard provides a graphical overview of all objects with dynamic charts.

![Object creation](readme/network-creation.gif)

Relevant parts of the doc: _[Object creation](http://enms.readthedocs.io/en/latest/objects/creation.html)_
Check it out for yourself: 


## Network visualization

Network visualization is of paramount importance for quickly understanding the network topology.
There are two ways of visualizing the network in eNMS:
- **Geographical view**: you can display the network in 2D or 3D, with Open Street Map or Google Map. A clusterized view is also available for large networks (> 10K nodes), for scalability.
- **Logical view**: the geographical view only makes sense if we have all GPS coordinates: it is not always the case. The logical view uses a graph-drawing algorithm to display the network in an aesthetically pleasing way.

![Network GIS visualization](readme/views.gif)

Networks can be exported on Google Earth from the geographical view: the resulting file is stored in the **_/kmz_** folder.

## Embedded SSH client

eNMS uses PuTTY to automatically establish an SSH connection to any SSH-enabled device from the web interface.
Your credentials are automatically provided to PuTTY for faster login.

![SSH connection](readme/ssh_connection.gif)

## Network automation

There are four types of task in eNMS:
- **Netmiko _configuration_ task**: list of commands to configure the device (plain text or Jinja2 template).
- **Netmiko _show commands_ task**: list of “show commands” which output will be displayed in the task logs.
- **NAPALM _configuration_ task**: partial or full configuration (plain text or Jinja2 template).
- **NAPALM _getters_**: list of getters which output will be displayed in the task logs.

For each task, you can select a list of target devices. A script is sent to all target devices at the same time, with multiple processes (`multiprocessing` library).

**Note**: netmiko has a _linux_ driver, which means that eNMS can also be used on Unix servers.

eNMS also provides some scheduling functions:
- **Start date**: instead of running the task immediately, the task will start at a specific time.
- **Frequency**: the task will be run periodically. This is especially useful for tasks that pull some information from the device, i.e netmiko **_show commands_** / **_NAPALM getters_** tasks.

### Simple configuration script with Netmiko

- Create a script in the _Script creation_ page.
- Set the script parameters (netmiko driver, global delay factor, target devices).

![Simple script with netmiko](readme/netmiko_simple.gif)

### Template-based configuration

For complex scripts, it is best to use Jinja2 templating language:
- Write a Jinja2 template in the _Script creation_ page.
- Import a YAML file that contains all associated variables.
eNMS will take care of converting the template to a real text-based script.

![Send jinja2 script via SSH with netmiko](readme/netmiko_j2.gif)

### NAPALM configuration

NAPALM is an automation framework that provides a set of functions to interact with different network device Operating Systems using a unified API.
NAPALM can be used to change the configuration (merge or replace), either via a plain text script or a Jinja2-enabled template.

**Note**: the NAPALM driver used by eNMS is the one you configure in the "Operating System" property of a node.
For NAPALM to work, you should respect NAPALM drivers syntax: `ios, iosxr, nxos, junos, eos`

![Use NAPALM to configure static routes](readme/napalm_config.gif)

### Netmiko _show commands_ periodic retrieval

You can schedule a task to retrieve the output of a list of commands (show, ping, traceroute, etc) periodically. The result is stored in the database and displayed in the logs of the task, in the _Task management_ page.

![Netmiko show](readme/netmiko_show.gif)

### NAPALM _getters_ periodic retrieval

You can also schedule a task to retrieve a NAPALM getter periodically.

![Configuration automation with NAPALM and Jinja2 scripting](readme/napalm_getters.gif)

### Comparison

For all periodic tasks, you can compare the results between any two devices, at two different times.

The comparison result is displayed with two methods:
- A **_unified diff_**: show just the lines that have changed plus a few lines of context, in an inline style. (like Git)
- A **_ndiff_**: list every line and highlights interline changes.

![Comparison](readme/comparison.gif)

## Display control with filters

The user can filter the objects available in the GUI by searching for specific value for each property. 
For each property, the user can choose to use a _regular expression_ instead of a hardcoded value:
regexes allows for specific search like a location or an IP subnet.

In the following example, we use the regexes `[france|spain]` for `location` to filter all objects that are not in France or in Spain, as well as the regex `[Router|Switch]` for `type` to filter all nodes that are neither a router, nor a switch.

![Object filtering](readme/object_filtering.gif)

Note that **_filters apply to everything_** in eNMS that uses objects: dashboard, object deletion,
geographical and logical views, task scheduling, etc. You can use them to visualize or send to script
to a specific subset of devices.

### Filtering use case

Let's imagine that you want to send a script to all routers with IOS 12.4(24)T or IOS 12.4(11)T. By default, all devices will be displayed in the _netmiko / napalm script scheduling_ page.

The first step will be to filters the nodes:
- go to the _Object filtering_ page
- set the "Operating System" to `IOS`
- set the "OS version" to `12.4\((24|11)\)T`
- tick the regex box for the "OS version" parameter
- apply the filter

After that, in the netmiko / napalm scheduling page, **_only the devices that match those criteria will be displayed_**: all devices in the multiple selection box can therefore be selected as target devices.

## TACACS+ authentication

It is possible to configure a TACACS+ server in eNMS: upon authentication, a request will be sent to the server to check the credentials and log in the user.

# Getting started

### (Optional) Set up a [virtual environment](https://docs.python.org/3/library/venv.html) 

### 1. Get the code
    git clone https://github.com/afourmy/eNMS.git
    cd eNMS

### 2. Install requirements 
    pip install -r requirements.txt

### 3. Run the code
    cd source
    python flask_app.py

### 4. Go the http://127.0.0.1:5100/

### 5. Create an account and log in

# Run eNMS in a docker container

### 1. Fetch the image on dockerhub
    docker pull afourmy/enms

### 2. Find the name of the docker image
    docker images

### 3. Run the image on port 5100
    docker run -p 5100:5100 image_name

# Contact

For any feedback, advice, feature request, join us on the [Network to Code slack](http://networktocode.herokuapp.com "Network to Code slack") (channel #enms)
