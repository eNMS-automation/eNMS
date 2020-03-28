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

Custom properties
-----------------

You can extend the properties of a device with your own properties. Custom properties are read
from a YAML file whose path must be set in the :ref:`Configuration`, section ``Paths``,
with the following variables:

  - ``type`` (**mandatory**): ``string``, ``integer``, ``float``, and ``boolean``
  - ``pretty_name`` (**optional**): Name of the property in the UI.
  - ``default`` (**optional**): Default value.
  - ``add_to_dashboard`` (**optional**): Whether the property should appear in the dashboard or not.
  - ``private`` (**optional**): If ``true``, the value will be stored in the Vault.
  - ``is_address`` (**optional**): Set to ``true`` if you want to property to be usable by GoTTY to
    connect to network devices (e.g hostnames, IP adddresses, etc)

.. note:: Custom properties must be defined once and for all before eNMS starts for the time,
  as they are part of the database schema.

You can find the following example in :guilabel:`eNMS / tests / customization`:

.. include:: ../../tests/customization/device_properties.yml
   :literal:
   :lines: 1-8
