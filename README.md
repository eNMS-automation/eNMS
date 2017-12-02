# Introduction

pyNMS-web is a network visualization, inventory and automation web application.

![pyNMS](https://github.com/mintoo/networks/raw/master/Readme/images/pynms.png)

# Getting started

The following modules are used in pyNMS:
```
flask (mandatory: GUI framework)
xlrd (desirable: used for saving projects)
netmiko, jinja2, NAPALM (optional: used for network automation)
```

In order to use pyNMS, you need to run **app.py**.
```
python app.py
```

# Features

## Network GIS visualization

Maps can be displayed in pyNMS to draw all network
devices at their exact location (longitude and latitude),
using the mercator or azimuthal orthographic projections.

![Network GIS visualization](https://github.com/mintoo/networks/raw/master/Readme/animations/gis_visualization.gif)

## Export to Google Earth

Networks can be exported as a .KML file to be displayed on Google Earth, with the same icons and link colors as in pyNMS.

![Google Earth](https://github.com/mintoo/networks/raw/master/Readme/images/google_earth_export.png)

## Network algorithmic visualization

GIS visualization can only be done if we have all GPS coordinates: it is not always the case.
Another way to visualize a network is use graph drawing algorithms to display the network.
The video below shows that the network converges within a few milliseconds to a visually pleasing shape (ring, tree, hypercube). 

![Network force-based visualization](https://github.com/mintoo/networks/raw/master/Readme/animations/graph_drawing.gif)

## Saving and import/export

Projects can be imported from / exported to an Excel or a YAML file. Any property can be imported, even if it does not natively exist in pyNMS: new properties are automatically created upon importing the project.

![Import and export a project (Excel / YAML)](https://github.com/mintoo/networks/raw/master/Readme/images/import_export.png)

## Embedded SSH client

pyNMS uses PuTTY to automatically establish an SSH connection to any SSH-enabled device (router, switch, server, etc).

![SSH connection](https://github.com/mintoo/networks/raw/master/Readme/animations/ssh_connection.gif)

## Send Jinja2 scripts to any SSH-enabled device

pyNMS uses Netmiko to send Jinja2 scripts to any device that supports SSH. 
Variables can be imported in a YAML file, and a script can be sent graphically to multiple devices at once with multithreading.

![Send jinja2 script via SSH with netmiko](https://github.com/mintoo/networks/raw/master/Readme/animations/send_script.gif)

## Interface to NAPALM

NAPALM is an automation framework that provides a set of functions to interact with different network device Operating Systems using a unified API. NAPALM can be used from within pyNMS to retrieve information about a device, and change the configuration.
You can click on the video for a step-by-step explanation of how it works.

[![Configuration automation with NAPALM and Jinja2 scripting](https://github.com/mintoo/networks/raw/master/Readme/animations/napalm_jinja2.gif)](https://www.youtube.com/watch?v=_kkW3jSQpzc)

## Searching objects

With the search function, the user can select a type of object and search a value for any property: all matching objects will be highlighted.
Regular expressions allows for specific search like an IP subnet.

![Searching objects](https://github.com/mintoo/networks/raw/master/Readme/animations/search.gif)

## Display control

## Site system

When network devices are located in the same building (e.g datacenters), they have the same GPS coordinates.
A site displays an internal view of the building, that contains all colocated devices.

![Site view](https://github.com/mintoo/networks/raw/master/Readme/animations/site_view.gif)

# Contact

You can contact me at my personal email address:
```
''.join(map(chr, (97, 110, 116, 111, 105, 110, 101, 46, 102, 111, 
117, 114, 109, 121, 64, 103, 109, 97, 105, 108, 46, 99, 111, 109)))
```

or on the [Network to Code slack](http://networktocode.herokuapp.com "Network to Code slack"). (@minto, channel #pynms)

# Credits

[Netmiko](https://github.com/ktbyers/netmiko "Netmiko"): A multi-vendor library to simplify Paramiko SSH connections to network devices.

[Jinja2](https://github.com/pallets/jinja "Jinja2"): A modern and designer-friendly templating language for Python.

[NAPALM](https://github.com/napalm-automation/napalm "NAPALM"): A library that implements a set of functions to interact with different network device Operating Systems using a unified API.

[simplekml](http://simplekml.readthedocs.io/en/latest/): Library to generate KML files (Google Earth)
