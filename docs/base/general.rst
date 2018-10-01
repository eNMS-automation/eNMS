============
What is eNMS
============

eNMS is an open source web application designed to help automate networks.
It encompasses the following aspects of network automation:

* **Configuration Management service**: commit / rollback of a configuration via Netmiko or Napalm.
* **Ansible Playbook service**: sending and managing ansible playbooks.
* **Custom services**: any python script is automatically detected by eNMS and added to the web UI.
* **Workflows**: all services can be organized in workflows.
* **Scheduling**: any service/workflow can be scheduled to run at a specific time, periodically or not.

Design philosophy
-----------------

eNMS provides a way to automate networks **graphically**, in a few simple steps:
    
1. Creation of the network (e.g by importing a spreadsheet describing the network topology).
#. Visualization of the network on a world map, or via a force-based algorithm.

.. image:: /_static/base/geographical_view.png
   :alt: 3D view
   :align: center

#. Creation of services and workflows.

.. image:: /_static/base/workflow.png
   :alt: A workflow
   :align: center

#. Scheduling of the service/workflow.

Application stack
-----------------

eNMS is built on the :guilabel:`Flask` Python framework and utilizes either a :guilabel:`SQLite` database, or a :guilabel:`PostgreSQL` database. It runs as a WSGI service behind your choice of HTTP server.

+----------------------------------------+------------------------------------+
|Function                                |Component                           |
+========================================+====================================+
|HTTP Service                            |nginx or Apache                     |
+----------------------------------------+------------------------------------+
|WSGI Service                            |gunicorn or uWSGI                   |
+----------------------------------------+------------------------------------+
|Application                             |Flask/Python                        |
+----------------------------------------+------------------------------------+
|Database                                |SQLite or PostgreSQL                |
+----------------------------------------+------------------------------------+
|Credentials storage                     |Hashicorp vault                     |
+----------------------------------------+------------------------------------+
|WebSSH connection                       |GoTTY                               |
+----------------------------------------+------------------------------------+