# Introduction

eNAPALM is a web interface to netmiko and NAPALM.
It allows to send scripts (plain text script or Jinja2 templates along with a YAML file) to one or more devices using netmiko or NAPALM, and to retrieve and store the output of NAPALM getters.
It also includes a daemon for the user to run specific actions (retrieve the getters, send a script) on a regular basis.

![eNAPALM](https://github.com/afourmy/e-napalm/blob/master/readme/napalm_configuration.png)

# Getting started

In order to start the website, you need to run `app.py`
```
python app.py
```

You can then access the website at http://IP:5100 where IP is the IP of the server (or http://127.0.0.1:5100 if you are running it locally).

# How to

## Device management

The first step is to create "devices". 
A device is defined by its hostname, IP address and operating system.
The left-side panel allows creating devices one by one by entering those parameters manually. Devices can also be created by importing an Excel file (.xls or .xlsx), or a CSV file.

![Device management](https://github.com/afourmy/e-napalm/blob/master/readme/manage_devices.png)

The device tab also includes a summary of all devices that have been created so far:
    
![List of all devices](https://github.com/afourmy/e-napalm/blob/master/readme/list_devices.png)

## Netmiko

The netmiko page provides an interface to Netmiko.
The user enter

# Contact

You can contact me at my personal email address:
```
''.join(map(chr, (97, 110, 116, 111, 105, 110, 101, 46, 102, 111, 
117, 114, 109, 121, 64, 103, 109, 97, 105, 108, 46, 99, 111, 109)))
```

or on the [Network to Code slack](http://networktocode.herokuapp.com "Network to Code slack"). (@minto)

# eNAPALM dependencies

eNAPALM relies on the following libraries:

* NAPALM
* netmiko
* jinja2
* pyYAML
* flask
* SQLAlchemy
* xlrd

Before using eNAPALM, you must make sure all these libraries are properly installed:

```
pip install napalm (dependencies: netmiko, jinja2, and pyYAML)
pip install flask_sqlalchemy (dependencies: flask)
pip install xlrd
```

# Credits

[Netmiko](https://github.com/ktbyers/netmiko "Netmiko"): A multi-vendor library to simplify Paramiko SSH connections to network devices.

[Jinja2](https://github.com/pallets/jinja "Jinja2"): A modern and designer-friendly templating language for Python.

[NAPALM](https://github.com/napalm-automation/napalm "NAPALM"): A library that implements a set of functions to interact with different network device Operating Systems using a unified API.
