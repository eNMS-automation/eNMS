============
Network view
============

Once the network has been created, it can be displayed on a geographical map.

All devices with a longitude and a latitude are displayed on a map at their exact location.
Devices have an ``icon`` property that defines which image is used, and links have a ``color`` property.

.. image:: /_static/views/network_view/network_view.png
   :alt: Classic 2D map
   :align: center

Tile layers
-----------

There are two types of tile layers available for the geographical display.

OpenStreetMap tiles
*******************

.. image:: /_static/views/network_view/osm_layer.png
   :alt: Open Street Map
   :align: center

Google Map tiles
****************

.. image:: /_static/views/network_view/google_map_layer.png
   :alt: Google Map
   :align: center

Marker Types
------------

There are three different types of markers: images, circle, and circle marker.
Images can take a lot of time to display if you have a big network; in that case, it is best to use circles or circle markers for scalability.

.. image:: /_static/views/network_view/circle_markers.png
   :alt: Circle Markers
   :align: center

You can change the type of marker and tiles from the right-click menu.
You can also configure, from the :guilabel:`Admin / Administration Panel` page, which are used by default when you open the view.
