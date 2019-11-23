=============
Search System
=============

All objects stored in the database are displayed in tables that you can filter using a search mechanism.

.. image:: /_static/advanced/search_system/filtering.png
   :alt: Filtering System.
   :align: center

Quick Search
************

For a quick search, you can use the textbox displayed above some of the columns in the table.
This search is **case-insensitive** and based on **inclusion**. ,

.. note:: If you enter ``a`` under ``Name``, eNMS will return all objects whose name contains ``a`` or ``A``.

.. note:: If you use several of these fields, all fields must match (boolean AND).

Advanced Search
***************

The first list in the "Advanced Search" panel lets you decide whether you want to display an object if **all** properties
are a match (boolean AND) or if **any** property is a match (boolean OR).

.. image:: /_static/advanced/search_system/advanced_filtering.png
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