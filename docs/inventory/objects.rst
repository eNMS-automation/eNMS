=======
Objects
=======

Type of objects
---------------

There are different types of devices and links available in eNMS.

* **Device**: router, switch, optical switch, server, host, antenna, regenerator, firewall.
* **Link**: ethernet link, optical link, etherchannel (LAG), optical channel, pseudowire, BGP peering.

Each type of device (resp. link) has a specific icon (resp. color) when displayed graphically:
    
.. image:: /_static/objects/objects/object_types.png
   :alt: Different types of objects
   :align: center

Creation
--------

Objects can be created from the :guilabel:`inventory/device_management` and :guilabel:`inventory/link_management` page, in two different ways:

* Manually, by entering the value of each property in a form (one by one).
* By importing an Excel file (.xls, .xlsx).

Manual creation
***************

Clicking on the ``Add a new device`` or ``Add a new link`` buttons will open a form with the list of all properties of the object.

Fill the form and click on the ``Submit`` button.

.. image:: /_static/objects/objects/object_creation.png
   :alt: Device and link creation forms
   :align: center

Creation via import
*******************

Objects can be created all at once by importing an Excel file. Devices must be defined in a spreadsheet called "Device" and links in a spreadsheet called "Link".
The first line of a spreadsheet contains the properties, the following lines define the objects, as demonstrated in the example below.

.. image:: /_static/objects/objects/import.png
   :alt: Example of excel spreadsheet for import
   :align: center

If you want to export the existing data out, you can export an Excel spreadsheet with all the object data filled out by clicking: ``Export network Topology``.

.. image:: /_static/objects/objects/export.png
   :alt: Export topology
   :align: center

.. note:: You can find examples of such spreadsheets in :guilabel:`eNMS/projects`.
.. note:: If an imported object already exists, its properties will be updated.

Creation via external API
*************************

Another way to create your network is to query an external API like OpenNMS or Netbox.
In :guilabel:`admin/administration`, you can find a form to query the OpenNMS API :
 
.. image:: /_static/objects/objects/opennms_api.png
   :alt: Export topology
   :align: center

  - ReST API: URL of the ReST API
  - Devices: URL of the devices that you want to import (this could be a subset of all available devices in the API, like ``https://demo.opennms.org/opennms/rest/nodes?foreignSource=OpenNMS_ATL``)
  - Type: Resulting eNMS type of the imported devices.
  - Login & Password: credentials of the ReST API.

Properties
----------

Some properties are mandatory:
 * Name: objects are uniquely defined by their name.
 * Source and destination: a link needs a source and a destination to be created.

.. tip:: In order to visualize the network topology on a map, devices must have geographical coordinates (longitude and latitude).