===========================
Keyboard and Mouse Bindings
===========================

For both the geographical and the logical views, bindings are the following :

* :guilabel:`Left-click (background)`: unselect all.
* :guilabel:`Left-click on a device`: open the property panel.
The property panel displays all properties of the object, and any property can be modified.
If the object is a device, it also contains a ``Connect`` button to automatically start an SSH terminal to the device.

.. image:: /_static/views/bindings/property_panel_properties.png
   :alt: Property panel: properties
   :align: center

If the SYSLOG server has been activated, eNMS stores all logs it receives.
The property panel also contains a ``Logs`` tab that displays all logs sent by this specific device.

.. image:: /_static/views/bindings/property_panel_logs.png
   :alt: Property panel: logs
   :align: center

* :guilabel:`Shift + left-click`: draw a selection rectangle to select multiple devices at once (geographical view only).

.. image:: /_static/views/bindings/multiple_selection.png
   :alt: Multiple selection
   :align: center

* :guilabel:`Right-click (background)`: Open the right-click menu (contains entries to change the type of view and tile layer).
