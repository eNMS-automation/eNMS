=================
Geographical view
=================

Once the network has been created, it can be displayed on a geographical map.

All devices are displayed at their exact location (they must have been created with a longitude and latitude) on the map. The icon of a device and the color of a link depend on their type.

Geographical display
--------------------

There are three types of geographical displays available.

2D map
******

The classic 2D map is based on the :guilabel:`Leaflet` JavaScript library.
All devices and links are displayed on a 2D representation of the Earth, based on the ``Google Mercator (EPSG:3857)`` projection.

The classic 2D map works well for small networks (less than 2000 devices), when there are no colocated devices (colocated devices cannot be distinguished from one another).

.. image:: /_static/views/geographical_view/2D_map.png
   :alt: Classic 2D map
   :align: center

Clusterized 2D map
******************

The clusterized 2D map is based on the :guilabel:`Leaflet MarkerCluster` JavaScript library.
Devices and links are displayed as clusters, whose size depends on the zoom level.

The clusterized map works well for large networks (up to 50000 devices), and it supports colocated devices.
Clicking on a group of colocated devices will expand the group.

.. image:: /_static/views/geographical_view/clusterized_map.png
   :alt: Clusterized 2D map
   :align: center

3D map
******

The 3D map is based on the :guilabel:`WebGL-Earth` JavaScript library (which itself uses :guilabel:`Cesium`)
All devices and links are displayed on a 3D representation of the Earth.

The 3D map works well for small networks (less than 500 devices) with no colocated devices.

.. image:: /_static/views/geographical_view/3D_map.png
   :alt: 3D map
   :align: center

Tile layers
-----------

There are three types of tile layers available for the geographical display.

OpenStreetMap tiles
*******************

.. image:: /_static/views/geographical_view/osm_layer.png
   :alt: Open Street Map
   :align: center

Google Map tiles
****************

.. image:: /_static/views/geographical_view/google_map_layer.png
   :alt: Google Map
   :align: center

NASA tiles
**********

.. image:: /_static/views/geographical_view/nasa_layer.png
   :alt: NASA
   :align: center

Switch between views
--------------------

The default view can be configured from the :guilabel:`Admin / Administration Panel` page.
You can switch to any view from the right-click menu.
