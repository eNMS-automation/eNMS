# Introduction

eNAPALM is a web interface to the two most widely used libraries for network automation: Netmiko and NAPALM.
It allows to send scripts (plain text script or Jinja2 templates) to one or more devices using Netmiko or NAPALM, and to retrieve and store the output of NAPALM getters.
It also includes a daemon for the user to run specific actions (retrieve the getters, send a script) on a regular basis.

![eNAPALM](https://github.com/afourmy/e-napalm/blob/master/readme/napalm_configuration.png)

# Getting started

In order to start the website, you need to run `app.py`
```
python app.py
```

You can then access the website at http://IP:5100 where IP is the IP of the server (or 127.0.0.1 if you are running it locally).

# How to

## Device management

![Device management](https://github.com/afourmy/e-napalm/blob/master/readme/manage_devices.png)

# Contact

You can contact me at my personal email address:
```
''.join(map(chr, (97, 110, 116, 111, 105, 110, 101, 46, 102, 111, 
117, 114, 109, 121, 64, 103, 109, 97, 105, 108, 46, 99, 111, 109)))
```

or on the [Network to Code slack](http://networktocode.herokuapp.com "Network to Code slack"). (@minto)

# eNAPALM dependencies

For the website, eNAPALM uses Flask, Bootstrap, SQLAlchemy and jQuery.
PyGIS relies on the following libraries:

* NAPALM.
* netmiko
* jinja2
* pyYAML


Before using PyGISS, you must make sure all these libraries are properly installed:

```
pip install napalm
```

# Credits

[NAPALM](https://github.com/napalm-automation): Network Automation and Programmability Abstraction Layer with Multivendor support. A Python library that implements a set of functions to interact with different router vendor devices using a unified API.
