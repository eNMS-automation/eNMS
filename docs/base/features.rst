========
Features
========
    
Creation of the network
-----------------------

Your network topology can be created manually or imported from an
external Source of Truth (OpenNMS, LibreNMS, or Netbox).
Once created, it is displayed in a sortable and searchable table.
A dashboard provides a graphical overview of your network with dynamic charts.

.. image:: /_static/base/features/inventory.png
   :alt: Inventory
   :align: center

.. image:: /_static/base/features/dashboard.png
   :alt: Dashboard
   :align: center

Network visualization
---------------------

eNMS can display your network on a world map (Google Map or Open Street Map).
Each device is displayed at its GPS coordinates.
You can click on a device to display its properties, configuration, or start an SSH terminal session.

.. image:: /_static/inventory/network_visualization/network_view.png
  :alt: Geographical View
  :align: center

Colocated devices can be grouped into geographical sites (campus, dacacenter, ...),
and displayed logically with a force-directed layout.

.. image:: /_static/inventory/network_visualization/site_view.png
   :alt: Logical view
   :align: center

Workflows
---------

Services can be combined into a workflow.
When a workflow is executed, its status is updated in real-time on the web UI.

.. image:: /_static/base/features/workflow.png
  :alt: Workflow Builder
  :align: center

Event-driven automation
-----------------------

While services can be run directly and immediately from the web UI,
you can also schedule them to run at a later time, or periodically by defining a frequency,
a start date and an end date. All scheduled tasks are displayed in a calendar.

.. image:: /_static/base/features/calendar.png
  :alt: Calendar
  :align: center

Services can also be executed programmatically:

  - eNMS has a REST API and a CLI interface that can be used to create, update and delete any type of objects,
    but also to trigger the execution of a service.
  - eNMS can be configured as a Syslog server, and rules can be created for syslog messages
    to trigger the execution of a service.

Configuration Management
------------------------

eNMS can work as a network device configuration backup tool and replace
Oxidized/Rancid with the following features:

  - Poll network elements and store the latest configuration in the database
  - Search for any text or regular-expression in all configurations
  - Download device configuration to a local text file
  - Use the REST API support to return a specified device’s configuration
  - Export all configurations to a remote Git repository (e.g. Gitlab) to view differences between various revisions of a configuration
