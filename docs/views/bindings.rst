========
Bindings
========

For both the geographical and the logical views, bindings are the following :

* :guilabel:`Left-click on a node`: selection of the node.
* :guilabel:`Double left-click on an object`: open the property panel.
The property panel displays all properties of the object, and any property can be modified.
If the object is a node, it also contains a ``Connect`` button to automatically start an SSH to the device.

.. image:: /_static/views/bindings/property_panel_properties.png
   :alt: Property panel: properties
   :align: center

If the SYSLOG server has been activated, eNMS stores all logs it receives.
The property panel also contains a ``Logs`` tabs that display all logs sent by this specific node.

.. image:: /_static/views/bindings/property_panel_logs.png
   :alt: Property panel: logs
   :align: center

* :guilabel:`Shift + left-click`: draw a selection rectangle to select multiple nodes at once.

.. image:: /_static/views/bindings/multiple_selection.png
   :alt: Multiple selection
   :align: center

* :guilabel:`Right-click`: Unselect all nodes.