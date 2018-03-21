================
Object filtering
================

The filtering system forces eNMS to consider only a subset of the network. Filters applies to everything: the dashboard (nodes and links diagrams), the object deletion forms, and most importantly, the graphical views.
A filter is a combination of user-defined values for the properties of an object.
If an object properties does not match **all** properties, it is filtered.
The forms used for filtering are available in  :guilabel:`objects/object_filtering`

Node filtering
--------------

.. image:: /_static/objects/filtering/node_filtering.png
   :alt: test
   :align: center

This filter enforces the following conditions:
 * name: ``node.*`` --- this regular expression matches all nodes which name starts with ``node``.
 * type: ``Router|Switch`` --- matches routers and switches (nodes which type is either ``Router``, or ``Switch``.
 * vendor: ``Cisco`` --- for this property, the regular expression box is not ticked. This means the value must be exactly ``Cisco``.

In summary, all Cisco routers or switches which name starts with ``node`` will match those conditions. All others will be filtered.

.. note:: All properties which field is left empty will be ignored.

Link filtering
--------------

.. image:: /_static/objects/filtering/link_filtering.png
   :alt: test
   :align: center

Example
--------

Filter by name
--------------

In this first example, we consider the following network:
    
.. image:: /_static/objects/filtering/network.png
   :alt: test
   :align: center

Unfiltered, this network results in the following view:

.. image:: /_static/objects/filtering/unfiltered_view.png
   :alt: test
   :align: center