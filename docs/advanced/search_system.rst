=============
Search System
=============

All objects stored in the database are displayed in tables that you can filter using the following options:

.. contents::
  :local:
  :depth: 1

|

Quick search
############
For a quick search, you can use the textbox displayed above columns in the table as pictured by the white magnifying glass.
In it's default state (Inclusion), this filter finds matches that include the text provided and is not case sensitive (i.e. a or A).
The drop down to the right of the magnifying glass has options to change the filter to return on exact matches (Equality), which is also not case sensitive.
And, the last quick filter option is based on a user provided Regular Expression.


.. image:: /_static/advanced/search_system/filtering.png
   :alt: Filtering System.
   :align: center




.. note:: If you use several of these fields the results will be based on all fields where input was provided. (i.e. it uses a boolean ``AND``).

|

Advanced search
###############
Additional filter criteria that will allow you to specify relationships between objects based on the following.

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
    - ``All``: match if related to all selected objects.
    - ``Unrelated``: match if not related to any of the selected objects.
    - ``None``: match if the are no related objects.

- **Standard properties**: You can filter based on inclusion, equality or a regular expression.

.. note:: The search based on regular expression only works if the database you are using supports it.
  PostgreSQL and MySQL support regular expressions, but SQLite does not.
