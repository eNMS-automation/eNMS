============
What is eNMS
============

eNMS is a vendor-agnostic NMS designed for building workflow-based network automation solutions.

It encompasses the following aspects of network automation:
- **Configuration Management Service**: Commit / Rollback of a configuration with Napalm or Netmio.
- **Ansible Service**: Sending and managing Ansible playbooks.
- **ReST Service**: Sending a ReST call (GET/POST/UPDATE/DELETE) with variable URL and payload.
- **Custom Services**: Any python script can be integrated into the web UI. If the script takes input parameters, a form will be automatically generated.
- **Workflows**: Services can be combined together graphically in a workflow.
- **Scheduling**: Services and workflows can be scheduled to start at a later time, or run periodically.
- **Event-driven automation**: Services and workflows can be triggered by an external event (ReST call or Syslog message).

Main features
-------------
    
1. Creation of the network

Nodes and links can be created either one by one, or all at once by importing an Excel spreadsheet. Once created, all objects are displayed in a sortable and searchable table, from which they can be edited and deleted. A dashboard provides a graphical overview of all objects with dynamic charts.

#. Network visualization

Once created, eNMS can display your network geographically on a 2D or 3D world map (with the tile layer of your choice: Open Street Map, Google Map...), and logically with d3.js. You can double-click on a node to display its properties, or start a Web SSH session to the device.

#. Service creation

eNMS comes with a number of "default services" leveraging libraries such as ansible, requests, netmiko, napalm to perform simple automation tasks. However, a service can be any python script. If your python script, takes input parameters, eNMS will automatically generate a form in the web UI.

To generate a form that matches your service, eNMS will perform the following conversion:

python string -> Text box.
python list -> Drop-down list (single or multiselect).
python bool -> Checkbox.
python dict -> Text box expecting a dictionnary.

Once created, you can create as many instances of your service as you need. Service instances can be executed, edited and deleted from the web UI.

#. Workflows
Services can be combined as a workflow. In a workflow, services can be connected with two types of edge: success edge and failure edge. The success edge (resp. failure edge) indicates which path to follow in the graph if the source script was successfully executed (resp. failed). When a workflow is executed, its status will be updated in real-time on the web UI.

#. Scheduling
Services and workflows can be run directly from the web UI. You can also schedule them to run at a later time, and periodically by defining a start date and an end date. All scheduled tasks are displayed in a calendar.

#. Event-driven automation
Event-driven automation in eNMS is twofold:
* eNMS has an internal ReST API that can be used to create, update and delete any type of objects (services, workflows, tasks), but also to trigger the execution of a service or a worflow with a POST request to the appropriate URL.
* eNMS can be configured as a Syslog server: all logs are stored in the database, and rules can be created to trigger the execution of a service or a workflow upon receiving a log matched by the rule.

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