# Introduction

eNMS is a network visualization, inventory and automation web platform.

![eNMS](https://github.com/afourmy/eNMS/blob/master/readme/eNMS.png)

# Features

## Network GIS visualization

Maps can be displayed in eNMS to draw all network devices at their exact location (longitude and latitude) with leaflet.js.

![Network GIS visualization](https://github.com/afourmy/eNMS/blob/master/readme/eNMS.png)

## Network algorithmic visualization

GIS visualization can only be done if we have all GPS coordinates: it is not always the case.
eNMS uses vis.js to visualize the network in an aesthetically pleasing way, with a force-based algorithm.

![Network force-based visualization](https://github.com/afourmy/eNMS/blob/master/readme/logical_view.png)

## Export to Google Earth

Networks can be exported as a .KML file to be displayed on Google Earth, with the same icons and link colors as in eNMS. (TODO)

## Saving and import/export

Projects (nodes and links with all properties) can be imported from an Excel file. 

## Embedded SSH client

eNMS uses PuTTY to automatically establish an SSH connection to any SSH-enabled device (router, switch, server, etc), from the web interface.

## Automation with Netmiko and NAPALM

### Netmiko support

eNMS uses Netmiko to send scripts to any device that supports SSH. 
Variables can be imported in a YAML file, and a script can be sent graphically to multiple devices at once with multithreading.

![Send jinja2 script via SSH with netmiko](https://github.com/afourmy/eNMS/blob/master/readme/netmiko.png)

### NAPALM support

NAPALM is an automation framework that provides a set of functions to interact with different network device Operating Systems using a unified API. NAPALM can be used from within eNMS to retrieve information about a device, and change the configuration.

[![Configuration automation with NAPALM and Jinja2 scripting](https://github.com/afourmy/eNMS/blob/master/readme/napalm_configuration.png)]

## Display control

In both the geographical and logical views, the user can filter the view by searching for specific value for each property. Regular expressions allows for specific search like an IP subnet.
The user can also control which property is displayed as a label for nodes and links.

(video: TODO)

# Getting started

The following modules are used in eNMS:
```
flask (mandatory: web framework)
xlrd, yaml (desirable: used for saving projects)
netmiko, jinja2, NAPALM (optional: used for network automation)
numpy, cvxopt (optional: used for linear programming)
simplekml (optional: used for exporting project to Google Earth)
```

In order to use eNMS, you need to run **/source/main.py**.
```
python main.py
```

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
