===============
Object creation
===============

Type of objects
---------------

There are different types of devices and links available in eNMS.

* **Device**: router, switch, optical switch, server, host, antenna, regenerator, firewall.
* **Link**: ethernet link, optical link, etherchannel (LAG), optical channel, pseudowire, BGP peering.

Each type of device (resp. link) has a specific icon (resp. color) when displayed graphically:
    
.. image:: /_static/objects/management/object_types.png
   :alt: Different types of objects
   :align: center

Creation
--------

Objects can be created from the :guilabel:`inventory/device_management` and :guilabel:`inventory/link_management` page, in two different ways:

* Manually, by entering the value of each property in a form. With this method, objects have to be created one by one.
* By importing an Excel file (.xls, .xlsx).

Manual creation
***************

Clicking on the ``Add a new device`` or ``Add a new link`` buttons will open a form with the list of all properties of the object.

Fill the form and click on the ``Submit`` button.

.. image:: /_static/objects/management/object_creation.png
   :alt: Device and link creation forms
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

.. tip:: In order to visualize the network topology on a map, devices must have geographical coordinates (longitude and latitude).