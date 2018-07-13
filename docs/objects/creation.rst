===============
Object creation
===============

Type of objects
---------------

There are different types of nodes and links available in eNMS.

* **Node**: Router, Switch, Optical switch, Server, Host, Antenna, Regenerator, Firewall.
* **Link**: Ethernet link, Optical link, Etherchannel (LAG), Optical channel, Pseudowire, BGP peering.

Each type of node (resp. link) has a specific icon (resp. color) when displayed graphically:
    
.. image:: /_static/objects/management/object_types.png
   :alt: Different types of objects
   :align: center

Creation
--------

Objects can be created from the :guilabel:`objects/object_management` page, in two different ways:

* Manually, by entering the value of each property in a form. With this method, objects have to be created one by one.
* By importing an Excel file (.xls, .xlsx).

Manual creation
***************

Clicking on the ``Add a new node`` or ``Add a new link`` buttons will open a form with the list of all properties of the object.

.. image:: /_static/objects/management/object_creation1.png
   :alt: Node and link creation
   :align: center

Fill the form and click on the ``Submit`` button.

.. image:: /_static/objects/management/object_creation2.png
   :alt: Node and link creation forms
   :align: center

Creation via import
*******************

All objects can be created at once by importing an Excel file. Each spreadsheet corresponds to a type of object.
The first line of a spreadsheet contains the properties, the following lines define the objects, as demonstrated in the example below.
If you want to export the existing data out, you can now export an Excel spreadsheet with all the object data filled out
by clicking: ``Export Network Topology``

.. image:: /_static/objects/management/import.png
   :alt: Example of excel spreadsheet for import
   :align: center

For eNMS to let you choose an Excel spreadsheet to import, click on the ``Import Network Topology`` button in the ``object_management`` page.

.. image:: /_static/objects/management/import_button.png
   :alt: Excel import button
   :align: center

.. note:: You can find examples of such spreadsheets in :guilabel:`eNMS/projects`.
.. note:: If an imported object already exists, its properties will be updated.

Properties
----------

Some properties are mandatory:
 * Name: objects are uniquely defined by their name.
 * Source and destination: a link needs a source and a destination to be created.

.. tip:: In order to visualize the network topology on a map, nodes must have geographical coordinates (longitude and latitude).