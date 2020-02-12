=============
Search System
=============

All objects stored in the database are displayed in tables that you can filter using a search mechanism.

.. image:: /_static/advanced/search_system/filtering.png
   :alt: Filtering System.
   :align: center

Quick Search
------------

For a quick search, you can use the textbox displayed above some of the columns in the table.
This search is **case-insensitive** and based on **inclusion**.

.. note:: If you enter ``a`` under ``Name``, eNMS will return all objects whose name contains ``a`` or ``A``.

.. note:: If you use several of these fields, all fields must match (boolean ``AND``).

Advanced Search
---------------

.. image:: /_static/advanced/search_system/advanced_filtering.png
   :alt: Advanced Filtering System.
   :align: center

- **Type of match**: Whether a match requires all properties to match (boolean ``AND``),
  or any of them (boolean ``OR``).

- **Relationships**: All tables stored in the database are associated by SQL relationships. For example, a pool
  contains devices and links and a device can belong to one or more pools: there is a many-to-many relationship
  between pools and devices. The advanced search system can perform a search based on these relationships. For a given relationship,
  you can choose between 3 types of match:

    - ``Any``: match if related to at least one of the selected objects.
    - ``Unrelated``: match if not related to any of the selected objects.
    - ``None``: match if the are no related objects.

- **Standard properties**: You can filter based on inclusion, equality or a regular expression.

.. note:: The search based on regular expression only works if the database you are using supports it.
  PostgreSQL and MySQL support regular expressions, but SQLite doesn't.

Example
*******