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