================
Network Creation
================

The network topology can be created in two different ways:

From the UI
-----------

By filling a form in :guilabel:`Inventory / Devices` and :guilabel:`Inventory / Links`.

.. note:: Some properties are mandatory:
 - Name: objects are uniquely defined by their name.
 - Source and destination: a link needs a source and a destination to be created.

.. note:: In order to visualize the network topology on a map,
  devices must have geographical coordinates (longitude and latitude).

From an Excel spreadsheet
-------------------------

Objects can be created all at once by importing an Excel spreadsheet in :guilabel:`Admin / Administration`,
section ``Topology Import``.
You can find examples of such spreadsheets in ``files`` / ``spreadsheets``. Y

.. note:: You can export an Excel spreadsheet containing the network topology by clicking on the ``Export`` button in the ``Topology Export`` column.
.. note:: If an imported object already exists, its properties will be updated.

Querying an external API
------------------------

Another way to create your network is to query an external API: OpenNMS, Netbox, or LibreNMS.
Check out the :ref:`Configuration` sections for each API, then click on the import button in the
:guilabel:`Admin / Administration`, column "Topology Import".

Custom properties
-----------------

You can extend the properties of a device with your own properties. Custom properties are read
from a YAML file whose path must be set in the :ref:`Configuration`, section ``Paths``,
with the following variables:

  - ``type`` (mandatory): ``string``, ``integer``, ``float``, and ``boolean``
  - ``pretty_name`` (optional): Name of the property in the UI.
  - ``default`` (optional): Default value.
  - ``add_to_dashboard`` (optional): Whether the property should appear in the dashboard or not.
  - ``private`` (optional): If ``true``, the value will be stored in the Vault.
  - ``is_address``: Set to ``true`` if you want to property to be usable by GoTTY to connect to address
    network device (e.g hostnames, IP adddresses, etc)

An example is provided in :guilabel:`eNMS / tests / customization / device_properties.yml`

.. include:: ../../tests/customization/device_properties.yml
   :literal:

.. note:: Custom properties must be defined once and for all before eNMS starts for the time,
  as they are part of the database schema.
