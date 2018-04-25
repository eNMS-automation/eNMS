============
What is eNMS
============

eNMS is an open source web application designed to help automate networks.
While network automation traditionally requires scripting skills, eNMS provides a way to automate networks **graphically**.
It encompasses the following aspects of network automation:

* **Configuration management**: commit/rollback of a configuration via NAPALM.
* **Netmiko scripting**: using netmiko to push a configuration, or display the result of a set of commands.
* **Ansible support**: sending and managing ansible playbooks.
* **Workflows**: all scripts can be organized in workflows (conditional graph of scripts executed in a specific order).
* **Scheduling**: any script/workflow can be scheduled to run at a specific time, periodically or not.

Design philosophy
-----------------

eNMS provides a way to automate networks **graphically**, in a few simple steps:
    
1. Creation of the network (e.g by importing a spreadsheet describing the network topology).
#. Creation of the scripts and workflows.
#. Visualization of the network on a world map, or via a force-based algorithm.
#. Selection of the target devices graphically, and scheduling of the script/workflow.

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
