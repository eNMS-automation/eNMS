================
Network Creation
================

The network topology can be created in two different ways:

From the UI
-----------

By filling a form in :guilabel:`Inventory / Devices` and :guilabel:`Inventory / Links` ("+" button)

.. image:: /_static/inventory/creation/creation_form.png
   :alt: Network Creation
   :align: center

.. note:: Some properties are mandatory:

  - Name: objects are uniquely defined by their name.
  - Source and destination: a link needs a source and a destination to be created.

.. note:: In order to visualize the network topology on a map,
  devices must have geographical coordinates (longitude and latitude).

From an Excel spreadsheet
-------------------------

The inventory can be imported from / exported to an Excel spreadsheet in the admin panel (see screenshot below),
section ``Inventory``.
You can find examples of such spreadsheets in ``files`` / ``spreadsheets``.

.. image:: /_static/inventory/creation/inventory_import.png
   :alt: Network Creation from Spreadsheet
   :align: center

.. note:: If you import an object that has already been created, its properties will be updated.

Querying an external API
------------------------

Another way to create your network is to query an external API: OpenNMS, Netbox, or LibreNMS.
You can do that by creating a "Topology Import" service from the ``Services`` page.

.. image:: /_static/inventory/creation/topology_import.png
   :alt: Network Creation via Topology Import
   :align: center

You can select an "Import Type" and fill the corresponding section of the form.
