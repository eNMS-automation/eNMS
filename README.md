# Introduction

eNMS is a network visualization, inventory and automation web platform.

**Find a demo of eNMS on this [website](http://afourmy.pythonanywhere.com/) !**

![eNMS](https://github.com/afourmy/eNMS/blob/master/readme/eNMS.png)

# Features

## Object creation

Nodes and links can be created in two ways: 
- one by one by specifying all properties manually, in the "Object creation" webpage
- by importing an Excel file with one sheet per type of object

![Object creation](https://github.com/afourmy/eNMS/blob/master/readme/object_creation.gif)

## Dashboard

![Dashboard](https://github.com/afourmy/eNMS/blob/master/readme/dashboard.gif)

## Network visualization

Maps can be displayed in eNMS to draw all network devices at their exact location (longitude and latitude) with leaflet.js.
GIS visualization can only be done if we have all GPS coordinates: it is not always the case.
eNMS uses vis.js to visualize the network in an aesthetically pleasing way, with a force-based algorithm.

![Network GIS visualization](https://github.com/afourmy/eNMS/blob/master/readme/views.gif)

## Export to Google Earth

Networks can be exported as a .KML file to be displayed on Google Earth, with the same icons and link colors as in eNMS.

![Export to Google Earth](https://github.com/afourmy/eNMS/blob/master/readme/google_earth.gif)

## Embedded SSH client

eNMS uses PuTTY to automatically establish an SSH connection to any SSH-enabled device (router, switch, server, etc), from the web interface.

![SSH connection](https://github.com/afourmy/eNMS/blob/master/readme/ssh_connection.gif)

## Automation with Netmiko and NAPALM

### Netmiko support

eNMS uses Netmiko to send scripts to any device that supports SSH. 

![Simple script with netmiko](https://github.com/afourmy/eNMS/blob/master/readme/netmiko_simple.gif)

Variables can be imported in a YAML file, and a script can be sent graphically to multiple devices at once with multithreading.

![Send jinja2 script via SSH with netmiko](https://github.com/afourmy/eNMS/blob/master/readme/netmiko_j2.gif)

### NAPALM support

NAPALM is an automation framework that provides a set of functions to interact with different network device Operating Systems using a unified API. NAPALM can be used from within eNMS to retrieve information about a device, and change the configuration.

[![Configuration automation with NAPALM and Jinja2 scripting](https://github.com/afourmy/eNMS/blob/master/readme/napalm_getters.gif)]

### Comparison

[![Comparison](https://github.com/afourmy/eNMS/blob/master/readme/comparison.gif)]

## Display control

In both the geographical and logical views, the user can filter the view by searching for specific value for each property. Regular expressions allows for specific search like an IP subnet.
The user can also control which property is displayed as a label for nodes and links.

[![Object filtering](https://github.com/afourmy/eNMS/blob/master/readme/object_filtering.gif)]

## Add a new property

- Open /eNMS/source/objects/models.py and add a Column to the appropriate model (Object, Node or Link)
Example: description = Column(String) in the Object class.
- Open /eNMS/source/objects/properties.py and add the property in the appropriate tuple.
- Open /eNMS/source/base/properties.py and add the property and it's user-friendly name in the "pretty_names" dictionnary.
- (Optional) If you want the new property to be displayed as a diagram in the dashboard, open /eNMS/source/objects/properties.py and add the property in the appropriate diagram tuple.
- Delete the database.db file, and restart the application.

# Getting started

The following modules are used in eNMS:
```
flask (web framework)
flask_wtf (forms)
flask_sqlalchemy (database)
flask_login (login system)
tacacs_plus (used for enabling TACACS+ authentication)
xlrd (used for creating objects from an Excel file)
netmiko, NAPALM (used for network automation)
jinja2, pyyaml (used for sending complex template-based scripts)
simplekml (used for exporting project to Google Earth)
```

In order to use eNMS, you need to run **/source/flask_app.py**.
```
python flask_app.py
```

# Contact

You can contact me at my personal email address:
```
''.join(map(chr, (97, 110, 116, 111, 105, 110, 101, 46, 102, 111, 
117, 114, 109, 121, 64, 103, 109, 97, 105, 108, 46, 99, 111, 109)))
```

or on the [Network to Code slack](http://networktocode.herokuapp.com "Network to Code slack"). (@minto, channel #enms)

# Credits

[Bootstrap](https://getbootstrap.com/ "Bootstrap"): Front-end HTML/CSS framework.

[eCharts](https://github.com/ecomfe/echarts "eCharts"): Interactive charting and visualization javascript library.

[Flask](http://flask.pocoo.org/ "Flask"): A microframework based on the Werkzeug toolkit and Jinja2 template engine.

[Flask WTForms](https://github.com/lepture/flask-wtf "Flask WTForms"): Simple integration of Flask and WTForms, including CSRF, file upload, and reCAPTCHA.

[Flask SQLAlchemy](http://flask-sqlalchemy.pocoo.org/ "Flask SQLAlchemy"): Adds support for SQLAlchemy to Flask.

[Flask Login](https://flask-login.readthedocs.io/en/latest/ "Flask Login"): Provides user session management for Flask.

[Jinja2](https://github.com/pallets/jinja "Jinja2"): A modern and designer-friendly templating language for Python.

[TACACS+](https://github.com/ansible/tacacs_plus/ "TACACS+"): A TACACS+ client that supports authentication, authorization and accounting.

[NAPALM](https://github.com/napalm-automation/napalm "NAPALM"): A library that implements a set of functions to interact with different network device Operating Systems using a unified API.

[Netmiko](https://github.com/ktbyers/netmiko "Netmiko"): A multi-vendor library to simplify Paramiko SSH connections to network devices.

[pyYAML](https://github.com/yaml/pyyaml "pyYAML"): YAML parser and emitter for Python.

[simplekml](http://simplekml.readthedocs.io/en/latest/ "SimpleKML"): Library to generate KML files (Google Earth).

[xlrd](https://github.com/python-excel/xlrd): Library to extract data from Microsoft Excel (tm) spreadsheet files.
