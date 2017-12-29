# Introduction

eNMS is a network visualization, ninventory ad automation web platform.

![eNMS](https://github.com/afourmy/eNMS/blob/master/readme/eNMS.png)

# Getting started

The following modules are used in eNMS:
```
flask (mandatory: web framework)
xlrd, yaml (desirable: used for saving projects)
netmiko, jinja2, NAPALM (optional: used for network automation)
numpy, cvxopt (optional: used for linear programming)
simplekml (optional: used for exporting project to Google Earth)
```

In order to use eNMS, you need to run **main.py**.
```
python main.py
```

# Features

## Network GIS visualization

Maps can be displayed in eNMS to draw all network
devices at their exact location (longitude and latitude),
using the mercator or azimuthal orthographic projections.

![Network GIS visualization](https://github.com/afourmy/eNMS/blob/master/readme/eNMS.png)

## Network algorithmic visualization

GIS visualization can only be done if we have all GPS coordinates: it is not always the case.
Another way to visualize a network is use graph drawing algorithms to display the network.
The video below shows that the network converges within a few milliseconds to a visually pleasing shape (ring, tree, hypercube). 

![Network force-based visualization](https://github.com/afourmy/eNMS/blob/master/readme/logical_view.png)

## Export to Google Earth

Networks can be exported as a .KML file to be displayed on Google Earth, with the same icons and link colors as in eNMS. (TODO)

## Saving and import/export

Projects can be imported from an Excel file. 

## Embedded SSH client

eNMS uses PuTTY to automatically establish an SSH connection to any SSH-enabled device (router, switch, server, etc).

## Send Jinja2 scripts to any SSH-enabled device

eNMS uses Netmiko to send Jinja2 scripts to any device that supports SSH. 
Variables can be imported in a YAML file, and a script can be sent graphically to multiple devices at once with multithreading.

![Send jinja2 script via SSH with netmiko](https://github.com/afourmy/eNMS/blob/master/readme/netmiko.png)

## Interface to NAPALM

NAPALM is an automation framework that provides a set of functions to interact with different network device Operating Systems using a unified API. NAPALM can be used from within eNMS to retrieve information about a device, and change the configuration.

[![Configuration automation with NAPALM and Jinja2 scripting](https://github.com/afourmy/eNMS/blob/master/readme/napalm_configuration.png)]

## Display control

With the search function, the user can select a type of object and search a value for any property: all matching objects will be highlighted.
Regular expressions allows for specific search like an IP subnet.
The user can select which type of device is displayed, use labels to display any property, and create graphical items like rectangles, ellipses or texts.

# Contact

You can contact me at my personal email address:
```
''.join(map(chr, (97, 110, 116, 111, 105, 110, 101, 46, 102, 111, 
117, 114, 109, 121, 64, 103, 109, 97, 105, 108, 46, 99, 111, 109)))
```

or on the [Network to Code slack](http://networktocode.herokuapp.com "Network to Code slack"). (@minto, channel #pyNMS)

# Credits

[Netmiko](https://github.com/ktbyers/netmiko "Netmiko"): A multi-vendor library to simplify Paramiko SSH connections to network devices.

[Jinja2](https://github.com/pallets/jinja "Jinja2"): A modern and designer-friendly templating language for Python.

[NAPALM](https://github.com/napalm-automation/napalm "NAPALM"): A library that implements a set of functions to interact with different network device Operating Systems using a unified API.

[simplekml](http://simplekml.readthedocs.io/en/latest/): Library to generate KML files (Google Earth)
