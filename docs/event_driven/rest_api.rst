========
ReST API
========

In this section, ``object`` refers to any device, link, service, workflow, or task in eNMS database.

eNMS has a ReST API allowing to:

- retrieve an object.
- delete an object
- create an object
- update an object
- run a Service instance or a Workflow.
- make sure eNMS is alive.

This ReST API allows other/external automation entities to invoke eNMS functions remotely/programmatically. In this way, eNMS can be integrated into a larger automation solution.

Retrieve or delete an object
****************************

::

 # via a GET or DELETE call to the following URL
 http://IP_address/rest/object/<object_type>/<object_name>

``<object_type>`` can be any of the following: ``device``, ``link``, ``user``, ``service``, ``workflow``, ``task``.
``<object_name>`` is to be replaced by the name of the object.

.. image:: /_static/automation/rest/get_object.png
   :alt: GET call to retrieve a device
   :align: center

Create or update an object
**************************

::

 # via a POST or PUT call to the following URL
 http://IP_address/rest/object/object_type

Execute a job (i.e a service, or a workflow)
********************************************

::

 # via a GET call to the following URL
 http://IP_address/rest/run_job/job_name

The job will run immediately.

Heartbeat
*********

::

 # Test that eNMS is still alive (used for high availability mechanisms)
 http://IP_address/rest/is_alive

eNMS returns ``True`` if it is still alive.
