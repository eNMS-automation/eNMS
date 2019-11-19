=========
Execution
=========

Run a service
-------------

You can run a service from:

- the "Service Management" or "Workflow Management" pages, by clicking on the "Run" or "Run with Updates" buttons
- the "Workflow builder" page, from the right-click menu.

There are two types of runs:

- Standard run (``Run`` button): uses the service properties during the run.
- Parametrized run (``Run with Updates`` button): a window is displayed with all properties initialized to the service
properties. You can change any property for the current run, but these changes won't be saved back to the service properties.

Run Notification
----------------

Type of notification
********************

When a service (or a workflow) finishes, you can choose to receive a notification that contains the logs of the service (whether it was successful or not for each device, etc).

There are three types of notification:

- Mail notification: eNMS sends a mail to an address of your choice.
- Slack notification: eNMS sends a message to a channel of your choice.
- Mattermost notification: same as Slack, with Mattermost.

To set up the mail system, you must set the following variables in the configuration:
``server``, ``port``, ``use_tls``, ``username``, ``sender``, ``recipients``.
Besides, you must set the password via the ``MAIL_PASSWORD`` environment variable.

The ``Mail Recipients`` parameter must be set for the mail system to work; the `Admin / Administration` panel parameter can
also be overriden from Step2 of the Service Instance and Workflow configuration panels. For Mail notification, there is
also an option in the Service Instance configuration to display only failed objects in the email summary versus seeing a
list of all passed and failed objects.

In Mattermost, if the ``Mattermost Channel`` is not set, the default ``Town Square`` will be used.

Parameters
**********

- "Send notification" (boolean)
- "Notification Method": choose among mail, slack or mattermost.
- "Notification header": will be displayed at the beginning of the notification.
- "Include Result Link in summary": whether the notification contains a link to the results.
- "Mail recipients": if left empty, the recipients defined in the administration panel will be used.
- "Display only failed nodes": the notification will not include devices for which the service ran successfully.

Results
-------

Real-time status update
***********************

Upon running a service, a log window will pop-up and show you the logs in real-time. When the run is over, the log window
will automatically disappear and the run results will be displayed instead.
You can go to the "Run Management" page to see what's happening in real-time: logs, current status, and progress
(if the service has device targets, eNMS tells you in real-time how many devices have been done and how many are left).

.. image:: /_static/runs/run_management.png
   :alt: Run management
   :align: center

Results of a run
****************

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
