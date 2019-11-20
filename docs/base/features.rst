========
Features
========
    
Creation of the network
-----------------------

Your network topology can be created manually (from the UI or an Excel spreadsheet) or imported from an
external Source of Truth (OpenNMS, LibreNMS, or Netbox).
Once created, it is are displayed in a sortable and searchable table.
A dashboard provides a graphical overview of your network with dynamic charts.

.. image:: /_static/base/features/inventory.png
   :alt: Inventory
   :align: center

.. image:: /_static/base/features/dashboard.png
   :alt: Dashboard
   :align: center

Network visualization
---------------------

Once created, eNMS can display your network on a world map with either the Google Map
or the Open Street Map tile layers. Each device is displayed on the map at its GPS coordinates.
Colocated devices can be grouped into geographical sites (campus, dacacenter, ...),
and displayed logically with a force-directed layout.
You can click on a device to display its properties or start a Web SSH terminal session.

.. image:: /_static/inventory/network_visualization/network_view.png
  :alt: Geographical View
  :align: center

.. image:: /_static/inventory/network_visualization/site_view.png
   :alt: Logical view
   :align: center

Workflows
---------

Services can be combined into a single workflow.
When a workflow is executed, its status will be updated in real-time on the web UI.

.. image:: /_static/base/features/workflow.png
  :alt: Workflow Builder
  :align: center

Scheduling
----------

While services and workflows can be run directly and immediately from the web UI,
you can also schedule them to run at a later time, or periodically by defining a frequency,
a start date and an end date. All scheduled tasks are displayed in a calendar.

.. image:: /_static/base/features/calendar.png
  :alt: Calendar
  :align: center

Configuration Management
------------------------

eNMS can work as a network device configuration backup tool and replace Oxidized/Rancid with the following features:
  - Poll network elements and store the latest configuration in the database
  - Search for any text or regular-expression in all configurations
  - Download device configuration to a local text file
  - Use the REST API support to return a specified device’s configuration
  - Export all configurations to a remote Git repository (e.g. Gitlab) to view differences between various revisions of a configuration

Event-driven automation
-----------------------

Event-driven automation in eNMS has two aspects:
  - eNMS has a REST API that can be used to create, update and delete any type of objects, but also to trigger the execution of a service or a workflow. 
  - eNMS can be configured as a Syslog server, and rules can be created for syslog messges to trigger the execution of a service or a workflow.
