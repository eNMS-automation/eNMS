================
Results of a run
================

Real-time status update
-----------------------

Upon running a service, a log window will pop-up and show you the logs in real-time. When the run is over, the log window
will automatically disappear and the run results will be displayed instead.
You can go to the "Run Management" page to see what's happening in real-time: logs, current status, and progress
(if the service has device targets, eNMS tells you in real-time how many devices have been done and how many are left).

.. image:: /_static/runs/run_management.png
   :alt: Run management
   :align: center

Results of a run
----------------

Results are stored for each run of the service / workflow.
The results are displayed as a JSON object. If the service ran on several device, you can display the results for a
specific device, or display the list of all "failed" / "success" device.
In the event that retries are configured, the Logs dictionary will contain an overall results section,
as well as a section for each attempt, where failed and retried devices are shown in subsequent sections
starting with attempt2.

You can compare two versions of the results by clicking on the ``Compare`` button (a line-by-line diff is generated).

.. image:: /_static/runs/run_results.png
   :alt: Results of a run
   :align: center
