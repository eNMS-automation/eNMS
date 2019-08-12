==============
Service result
==============

Real-time status update
-----------------------

Service results
---------------

Results are stored for each run of the Service Instance (and for Workflows at large).
The results are displayed as a JSON object. If the job ran on several device, you can display the results for a
specific device, or display the list of all "failed" / "success" device.
In the event that retries are configured, the Logs dictionary will contain an overall results section,
as well as a section for each attempt, where failed and retried devices are shown in subsequent sections
starting with attempt2.

You can compare two versions of the logs from the ``Logs`` window (a line-by-line diff is generated).
Here's a comparison of a ``Napalm get_facts`` service:

.. image:: /_static/services/service_system/service_compare_logs.png
   :alt: Compare logs
   :align: center

Gitlab Export
-------------

In the :guilabel:`admin/administration` page, you can configure a remote Git repository with the property ``Git Repository Automation``. Each service has a ``Push to Git`` option to push the results of the service to this remote repository.
This allows comparing the results of a service between any two runs.