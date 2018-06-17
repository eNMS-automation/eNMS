========
ReST API
========

eNMS has a ReST API allowing to:

- retrieve an object.
- execute a task.

Retrieve an object
******************

::

 # via a GET call to the following URL
 http://IP_address/rest/get/object_type/object_name

``object_type`` can be any of the following: ``node``, ``link``, ``user``, ``script``, ``workflow``, ``task``.

.. image:: /_static/automation/rest/get_object.png
   :alt: GET call to retrieve a node
   :align: center

Execute a task
**************

::

 # via a GET call to the following URL
 http://IP_address/rest/execute_task/task_name

The task will start immediately (and its properties are displayed).

.. image:: /_static/automation/rest/start_task.png
   :alt: GET call to execute a task
   :align: center
