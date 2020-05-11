=====
Pools
=====

The Pools feature allow the user to create groups of Device or Link objects. They can be used to filter the Pool Inventory table
and in the :guilabel:`Visualization -> Network` view screen. Pools are also used to target an automation task to a specific, defined,
group ("pool") of devices. A pool is defined as a combination of properties values of device or link  object. When defining a Pool,
for each property value, decide, whether the match is based on inclusion, equality, or regular expression.

If the properties of a device or link object matches the pool properties, that object will be automatically added to the pool.

Pool Management
---------------

Pools can be created, updated, duplicated and deleted from :guilabel:`Inventory -> Pools`. They can be edited to manually
select devices and links instead of using criteria based on properties.

.. image:: /_static/inventory/pools/pool_table.png
   :alt: Pool Management
   :align: center

A logical view of a pool can be displayed using the ``Internal View`` button.

.. image:: /_static/inventory/pools/pool_visualization.png
   :alt: Pool Internal View
   :align: center

Device Pool creation example
----------------------------

.. image:: /_static/inventory/pools/device_filtering.png
   :alt: Device Filtering
   :align: center

This pool enforces the Union of the following conditions:
 * name: ``Washington.*`` --- Match is Inclusion; all devices whose name include ``Washington`` will be selected
 * subtype: ``GATEWAY|PEER`` --- Match is Regular Expression; all devices having subtype ``GATEWAY`` and ``PEER`` will be selected
 * vendor: ``Cisco`` --- Match is Equality; all devices whose vendor is ``Cisco`` will be selected

In summary, all ``Cisco`` ``GATEWAY and PEER`` whose name begins with ``Washington`` will match these conditions, and they will be
members of the pool.

.. note:: All properties left with empty fields are simply ignored.
.. note:: Along with all properties of a device, you can use the device **Configuration** and 
  **Operational Data** as a constraint for the pool. Refer to the Configuration Management page
  for more information.

Links Pool creation example
---------------------------

.. image:: /_static/inventory/pools/link_filtering.png
   :alt: Link filtering
   :align: center

This pool enforces the union of the following conditions:
 * subtype: ``Ethernet link`` --- Match is Equality; all Ethernet links will be selected
 * source name: ``Washington.*`` --- Match is Inclusion; all links whose source is the device name include ``Washington`` will be selected

In summary, all ``Ethernet`` links starting from devices with name that include ``Washington`` will be members of the pool.

Default Pools
-------------

Three pools are created by default in eNMS:

- "All objects": A pool that matches all Devices and Links.
- "Devices only": A pool that matches all Devices, no Links.
- "Links only": A pool that matches all Links, no Device.

Pools based on Configuration
----------------------------

Pools can be created by searching the configurations data collected from all of the devices, rather than just the
Inventory parameters for each device. Configuration collection must be, first, configured and then allowed to run
at least once before the configurations can be searched upon for the Pool.

Filter the view with a Pool
---------------------------

Pools can be used as filters for Devices and Links tables on the geographical views :guilabel:`Visualization -> Network`. At the
top of the screen, click on the filter button ``Devices`` or ``Link`` to open the "Filtering" panel. Both of these panels
contain a ``Pools`` drop-down list (multiple selection) to filter objects in the view. Click the refresh button after
selecting filter criteria.

.. image:: /_static/inventory/pools/view_filter.png
   :alt: Pool filtering of the view
   :align: center

Use a Pool as target of a Service or a Workflow
-----------------------------------------------

In "Step 3", select Device(s) and/or Pool(s) as target(s).

.. image:: /_static/inventory/pools/target_pool.png
   :alt: Use a pool as a target
   :align: center

Use a Pool to restrict a user to a subset of objects
----------------------------------------------------

From the :guilabel:`Admin / User Management` panel, you can select a pool used as a database filtering
mechanism for a particular user.
All mechanisms and all pages in eNMS will be restricted to the objects of that pool for that particular user.
The exception is Service and Workflows that have been already configured to run against a particular
set of devices and links. If those devices and links are outside of the pool that the user is restricted to,
the user will still be able to see them.

Pool recalculation
------------------

All Pools are subject to automatic updates by eNMS (contingent upon the fact that its 'Manually Defined' flag is NOT
set) after creation:

- When the eNMS starts up or restarts
- When a device is manually added to the inventory
- When a device is modified
- When, after pulling or cloning the content from the git configuration repository
- When a service runs that has `Update pools before running` selected in Step 3 Targets
- When the `poller service` runs (service responsible for fetching all device configurations), ONLY the pools for which the device ``Current Configuration`` are not empty, are updated.

To manually update a Pool:

- Click on the ``Update`` button of a desired pool in Pool Management table listing
- Click on the ``Update all pools`` button at the top of Pool Management UI

Manual definition and "Manually Defined" option
-----------------------------------------------

Initially, by default, the devices and links within a pool are determined based on the pool properties. The individual
pools can be edited by allowing the user to define the devices and links by selecting them directly and there are a
couple of ways of doing this:

- Click on ``edit`` icon: Will allow user to modify the Device Properties and Link Properties.
- Click on ``wrench`` icon: Will open a "Pool Object" screen to allow a user to copy/pasting a string of comma separated devices and links names as well as selecting devices and links from a drop-down menu field.

.. image:: /_static/inventory/pools/manual_definition.png
   :alt: Manual definition of a pool
   :align: center

.. note:: Pools with manually selected objects need to have the 'Manually Defined' checkbox selected.
  This prevents manually selected pools from being re-calculated based on pool criteria.
  If the user wants to run against a pool that has some criteria specified as well as some manually
  specified devices, it is advised to have 2 pools, one with the criteria specified and another with
  the manually selected devices. When running a service, multiple pools and multiple devices can be
  specified, and the service will run against all specified objects.
