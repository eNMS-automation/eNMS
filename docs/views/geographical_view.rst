=================
Geographical view
=================

Once the network has been created, it can be displayed on a geographical map.

All nodes are displayed at their exact location (they must have been created with a longitude and latitude) on the map. The icon of a node and the color of a link depend on their type.

Geographical display
--------------------

There are three types of geographical displayed available.

2D map
******

The classic 2D map is based on the :guilabel:`Leaflet` JavaScript library.
All nodes and links are displayed on a 2D representation of the Earth, based on the ``Google Mercator (EPSG:3857)`` projection.

The classic 2D map works well for small networks (less than 5000 nodes), with no colocated nodes (colocated nodes are indistinguishable from one another).

.. image:: /_static/views/2D_map.png
   :alt: test
   :align: center

Clusterized 2D map
******************

The clusterized 2D map is based on the :guilabel:`Leaflet MarkerCluster` JavaScript library.
Nodes and links are displayed as clusters, which size depends on the zoom level.

The clusterized map works well for large networks (until 50000 nodes), and it supports colocated nodes.
Clicking on a group of colocated nodes will expand the group.

.. image:: /_static/views/clusterized_map.png
   :alt: test
   :align: center

3D map
******

The 3D map is based on the :guilabel:`WebGL-Earth` JavaScript library (which itself uses :guilabel:`Cesium`)
All nodes and links are displayed on a 3D representation of the Earth.

The classic 2D map works well for small networks (less than 500 nodes) with no colocated nodes.

.. image:: /_static/views/3D_map.png
   :alt: test
   :align: center

Tile layers
-----------

There are three types of tile available for the geographical display.

OpenStreetMap tiles
*******************

