# Introduction

eNAPALM is a web interface for NAPALM and Netmiko.
It allows to send scripts (plain text script or Jinja2 templates along with a YAML file) to one or more devices using netmiko or NAPALM, and to retrieve and store the output of NAPALM getters.

It also includes a daemon, implemented with APScheduler, for the user to retrieve NAPALM getters on a regular basis (every hour, every day, etc) or to send a script at a given point in time.

eNAPALM is implemented with Flask, Bootstrap, jQuery, SQL Alchemy (database) and AP Scheduler (crontab-like functionnalities).

![eNAPALM](https://github.com/afourmy/e-napalm/blob/master/readme/napalm_configuration.png)

# Getting started

In order to start the website, you need to run `app.py`
```
python app.py
```

You can then access the website at http://IP:5100 where IP is the IP address of the server (or http://127.0.0.1:5100 if you are running it locally).

# How to

## Device management

The first step is to create "devices". 
A device is defined by its hostname, IP address and operating system.
The left-side panel allows creating devices one by one by entering those parameters manually. Devices can also be created by importing an Excel file (.xls or .xlsx), or a CSV file.

![Device management](https://github.com/afourmy/e-napalm/blob/master/readme/manage_devices.png)

The device tab also includes a summary of all devices that have been created so far:
    
![List of all devices](https://github.com/afourmy/e-napalm/blob/master/readme/list_devices.png)

## NAPALM Configuration

The NAPALM configuration webpage allows the user to change the configuration of one or more devices by using NAPALM functions: load_merge, load_replace, commit, discard and rollback.
The user has to select a port (default port: 8022) and a transport protocol.
The script can also be a Jinja2 template, in which case a YAML file has to be imported to turn the J2 template into a real script.

In the right-side panel, it is possible to schedule the time when the script will be sent to the device(s). 
If left blank, the script will be sent immediately.

![NAPALM Configuration](https://github.com/afourmy/e-napalm/blob/master/readme/napalm_configuration.png)

See [NAPALM tutorial](https://napalm.readthedocs.io/en/latest/tutorials/first_steps_config.html "NAPALM tutorial") for more information about those functions.

## NAPALM Getters

The user can choose a device and a set of getters. The query will be sent to the device and the output displayed in the middle panel. 

The getters output can also be retrieved and stored on the server periodically, by selecting a frequency in the right-side panel. The output will be stored in the 'getters' folder of the application.

![NAPALM Getters](https://github.com/afourmy/e-napalm/blob/master/readme/napalm_getters.png)

More information about getters in [NAPALM tutorial](https://napalm.readthedocs.io/en/latest/base.html "NAPALM tutorial").

## Netmiko

The netmiko page provides an interface to Netmiko.
The user select a driver and target devices, enters its credentials (username, password and secret password if needed), and sets the port and the global delay factor (default: 8022, 1).
Just like for NAPALM, the script can be a Jinja2 template (YAML file to be imported).

![Netmiko](https://github.com/afourmy/e-napalm/blob/master/readme/netmiko.png)

# eNAPALM dependencies

eNAPALM relies on the following libraries:

* NAPALM
* netmiko
* jinja2
* pyYAML
* flask
* flask_sqlalchemy
* flask_apscheduler
* xlrd

Before using eNAPALM, you must make sure all these libraries are properly installed:

```
pip install napalm (dependencies: netmiko, jinja2, and pyYAML)
pip install flask_sqlalchemy (dependencies: flask)
pip install flask_apscheduler
pip install xlrd
```

or 

```
pip install -r requirements.txt
```

# Credits

[NAPALM](https://github.com/napalm-automation/napalm "NAPALM"): A library that implements a set of functions to interact with different network device Operating Systems using a unified API.

[Netmiko](https://github.com/ktbyers/netmiko "Netmiko"): A multi-vendor library to simplify Paramiko SSH connections to network devices.

[Jinja2](https://github.com/pallets/jinja "Jinja2"): A modern and designer-friendly templating language for Python.

[xlrd](https://github.com/python-excel/xlrd) Library to extract data from Microsoft Excel (tm) spreadsheet files

[Flask](http://flask.pocoo.org) Micro webdevelopment framework for Python.

[SQLAlchemy](https://www.sqlalchemy.org) Python SQL toolkit and Object Relational Mapper

[flask_apscheduler](https://github.com/viniciuschiele/flask-apscheduler) Adds APScheduler (Advanced Python Scheduler) support to Flask