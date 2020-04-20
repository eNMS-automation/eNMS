============
What is eNMS
============

eNMS is a vendor-agnostic NMS designed for building workflow-based network automation solutions.

.. image:: /_static/base/workflow.png
   :alt: eNMS Introduction
   :align: center

It encompasses the following aspects of network automation:

  - **Configuration Management Service**: Backup with Git, change and rollback of configurations.
  - **Validation Services**: Validate data about the state of a device with Netmiko and NAPALM.
  - **Ansible Service**: Store and run Ansible playbooks.
  - **REST Service**: Send REST calls with variable URL and payload.
  - **Python Script Service**: Any python script can be integrated into the web UI. 
    eNMS will automatically generate a form in the UI for the script input parameters.
  - **Workflows**: Services can be combined together graphically in a workflow.
  - **Scheduling**: Services and workflows can be scheduled to start at a later time, or run periodically with CRON.
  - **Event-driven automation**: Services and workflows can be triggered by an external event (REST call, Syslog message, etc).

Application stack
-----------------

+----------------------------------------+------------------------------------+
|Function                                |Component                           |
+========================================+====================================+
|HTTP Service                            |nginx                               |
+----------------------------------------+------------------------------------+
|WSGI Service                            |gunicorn                            |
+----------------------------------------+------------------------------------+
|Application                             |Flask/Python 3.6+                   |
+----------------------------------------+------------------------------------+
|Database                                |SQLite, MySQL or PostgreSQL         |
+----------------------------------------+------------------------------------+
|Credentials storage                     |Hashicorp vault                     |
+----------------------------------------+------------------------------------+

.. toctree::
   :maxdepth: 2
   :caption: Getting started

   base/features
   base/installation
   base/release_notes

.. toctree::
   :maxdepth: 2
   :caption: Inventory

   inventory/network_creation
   inventory/pools
   inventory/web_connection
   inventory/network_visualization

.. toctree::
   :maxdepth: 2
   :caption: Automation

   automation/services
   automation/default_services
   automation/workflows
   automation/scheduling

.. toctree::
   :maxdepth: 2
   :caption: Advanced

   advanced/search_system
   advanced/configuration_management
   advanced/rest_api
   advanced/administration
   advanced/contributing
