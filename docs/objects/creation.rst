===============
Object creation
===============

Type of objects
---------------

There are different types of nodes and links available in eNMS.

* **Node**: Router, Switch, Optical switch, Server, Host, Antenna, Regenerator, Firewall.
* **Link**: Ethernet link, Optical link, Etherchannel (LAG), Optical channel, Pseudowire, BGP peering.

Each type of node (resp. link) has a specific icon (resp. color) when displayed graphically:
    
.. image:: /_static/objects/object_types.png
   :alt: test
   :align: center

Creation
--------

Objects can be created from the :guilabel:`objects/object_creation` menu, in two different ways:

* Manually, by entering the value of each property in a form. This method is rather slow as objects have to be created one by one.
* By importing an Excel file (.xls, .xlsx).

Manual creation
***************

To create an object, simply fill the form and click submit. 

.. image:: /_static/objects/creation.png
   :alt: test
   :align: center

.. note:: These forms can also be used to update the properties of an object. If you fill the form with the name of an already existing object and click on submit, tche object properties will be modified acordingly (all empty fields are ignored).

Creation via import
*******************

All objects can be created at once by importing an Excel file.
Each spreadsheet corresponds to a type of object.
The first line of a spreadsheet contains the properties, the following lines define the objects, as demonstrated in the example below.

.. image:: /_static/objects/import.png
   :alt: test
   :align: center

.. note:: Like for the manual creation, if an imported object already exists, its properties will be updated.

Properties
----------

Some properties are mandatory:
 * Name: objects are uniquely defined by their name.
 * Source and destination: a link needs a source and a destination to be created.

.. tip:: In order to visualize the network topology on a map, nodes must have geographical coordinates (longitude and latitude).