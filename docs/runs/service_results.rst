================
Results of a run
================

Real-time status update
-----------------------

Upon running a job, a log window will pop-up and show you the logs in real-time.
You can go to the "Run Management" page to see what's happening in real-time: logs, current status, and progress
(if the service has device targets, eNMS tells you in real-time how many devices have been done and how many are left).

.. image:: /_static/runs/run_management.png
   :alt: Run management
   :align: center

Results of a run
----------------

Results are stored for each run of the service / workflow.
The results are displayed as a JSON object. If the job ran on several device, you can display the results for a
specific device, or display the list of all "failed" / "success" device.
In the event that retries are configured, the Logs dictionary will contain an overall results section,
as well as a section for each attempt, where failed and retried devices are shown in subsequent sections
starting with attempt2.

You can compare two versions of the results by clicking on the ``Compare`` button (a line-by-line diff is generated).

.. image:: /_static/runs/run_results.png
   :alt: Results of a run
   :align: center

Gitlab Export
-------------

In the :guilabel:`admin/administration` page, you can configure a remote Git repository with the property ``Git Repository Automation``. Each service has a ``Push to Git`` option to push the results of the service to this remote repository.
This allows comparing the results of a service between any two runs.