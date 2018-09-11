============
Object pools
============

Pools allows to create groups of devices. They can be used to filter the view, and to target an automation task to a specific subset of devices.
A pool is defined as a combination of values (or regular expressions) for the properties of an object. 

If the properties of an object matches **all** properties of the pool, the object will belong to the pool.
 
Pools can be created in :guilabel:`inventory/pool_management`.

A first example
---------------

.. image:: /_static/objects/filtering/node_filtering.png
   :alt: test
   :align: center

This pool enforces the following conditions:
 * name: ``node.*`` --- this regular expression matches all nodes which name starts with ``node``.
 * type: ``Router|Switch`` --- matches routers and switches (nodes which type is either ``Router``, or ``Switch``.
 * vendor: ``Cisco`` --- for this property, the regular expression box is not ticked. This means the value must be exactly ``Cisco``.

In summary, all Cisco routers or switches which name starts with ``node`` will match these conditions, and they will be a member of the pool.

.. note:: All properties which field is left empty are simply ignored.

A pool of link
--------------

.. image:: /_static/objects/filtering/link_filtering.png
   :alt: test
   :align: center

This pool enforces the following conditions:
 * type: ``Ethernet link`` --- matches all Ethernet links.
 * source: ``bnet6`` --- matches all links which source is the node ``bnet6``.

In summary, all Ethernet links starting from the node ``bnet6`` will be part of the pool.

Filter the view with a pool
---------------------------

Pools can be used as filters for the geographical and logical views.
You can switch between pools with the drop-down list in the top-right corner of the screen (framed in red below).

.. image:: /_static/objects/filtering/apply_filter.png
   :alt: Apply a filter
   :align: center

Let's consider the following network:

.. image:: /_static/objects/filtering/network.png
   :alt: test
   :align: center

Unfiltered, this network results in the following view:

.. image:: /_static/objects/filtering/unfiltered_network.png
   :alt: test
   :align: center

We create a pool with a condition on the ``Name`` of a link:

.. image:: /_static/objects/filtering/filter_all_links.png
   :alt: test
   :align: center

There isn't a single link which name is ``a``: all links will be filtered.

Filtering the view with this pool will result in the following display:

.. image:: /_static/objects/filtering/network_filter1.png
   :alt: test
   :align: center    

We add a new condition on the ``Location`` of a node to exclude all nodes that are located outside of France or spain:

.. image:: /_static/objects/filtering/filter_location.png
   :alt: test
   :align: center

This result in the following view:

.. image:: /_static/objects/filtering/network_filter2.png
   :alt: test
   :align: center    

Restrict to nodes with IOS-XE or IOS-XR
***************************************

Finally, out of the remaining nodes, we exclude all nodes which operating system is not IOS-XE or IOS-XR:

.. image:: /_static/objects/filtering/filter_os.png
   :alt: test
   :align: center

This results in the following view:

.. image:: /_static/objects/filtering/network_filter3.png
   :alt: test
   :align: center 

.. note:: Using the pool system is important because the targets of a script in eNMS can be a pool (or a group of pools). Therefore, pools can be used as a way to apply a script to a specific group of devices.