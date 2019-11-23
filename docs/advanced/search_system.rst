=============
Search System
=============

All network devices are displayed in a table where they can be edited and deleted, 
and filtered. There are two filtering systems.

.. image:: /_static/inventory/network_creation/table_filtering.png
   :alt: Filtering System.
   :align: center

Quick search
************

For a quick search, you can use the textbox displayed above some of the columns in the table.
This search is case-insensitive and based on **inclusion**. If you enter a value in several of these fields,
the results is the list of objects that match all fields (boolean AND).
If you enter "a" in the textbox above "Location" in the "Device Management" table, eNMS will return all devices
for which the location contains either "a" or "A".

Advanced search
***************

The first list in the "Advanced Search" panel lets you decide whether you want to display an object if **all** properties
are a match (boolean AND) or if **any** property is a match (boolean OR).

.. image:: /_static/inventory/network_creation/advanced_filtering.png
   :alt: Filtering System.
   :align: center

The advanced search lets you decide, for each property, whether you want to filter based on inclusion, equality
or a regular expression.

.. note:: The search based on regular expression only works if the database you are using supports it. PostgreSQL and MySQL support regular expressions, but SQLite doesn't.

Besides, the advanced search also lets you filter based on **relationships**.

For example, a device has 3 types of relationships:

- services: indicates whether or not the device is a target of a given service (service or workflow)
- pools: indicates whether or not the device is a target of a given pool.
- links: indicates whether the device is the source or the destination of a link.

You can select services, pools and links in the "Advanced Search" panel for a device, and only the device that are a match
for the relationship will be displayed in the results.

You can use the "Clear Search" button above the table to return to the initial state (no filter).