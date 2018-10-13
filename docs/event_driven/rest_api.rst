========
ReST API
========

eNMS has a ReST API allowing to:

- retrieve an object.
- delete an object
- create an object
- update an object
- execute a task.

This ReST API allows other/external automation entities to invoke eNMS functions remotely/programmatically. In this way, eNMS can be integrated into a larger automation solution.

Retrieve or delete an object
****************************

::

 # via a GET or DELETE call to the following URL
 http://IP_address/rest/object/object_type/object_name

``object_type`` can be any of the following: ``device``, ``link``, ``user``, ``service``, ``workflow``, ``task``.

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
