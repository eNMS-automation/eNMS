========================
Execution and Scheduling
========================

Running a service
-----------------

You can run a service from the "Services" page ("Run" button) or from the "Workflow Builder"
(right-click menu).

There are two types of runs:

- Standard run: uses the service properties during the run.
- Parametrized run: a window is displayed with all properties initialized to the service
properties. You can change any property for the current run, but these changes won't be saved
back to the service properties.

Results
-------

Results are stored for each run of the service / workflow.
The results are displayed as a JSON object. If the service ran on several device, you can display the results for a
specific device, or display the list of all "failed" / "success" device.
In the event that retries are configured, the Logs dictionary will contain an overall results section,
as well as a section for each attempt, where failed and retried devices are shown in subsequent sections
starting with attempt2.

Scheduling
----------

Instead of running services immediately, they can be scheduled by creating a task, from :guilabel:`Scheduling / Tasks`.
You need to enter a name, which service you want the task to execute, and a scheduling mode.
There are two scheduling modes:
  - Date Scheduling: enter a start date and optionally a frequency and an end date.
    If a ``Frequency`` is defined without an end date, the service will keep running until manually stopped.
  - Cron Scheduling: enter a crontab expression.

.. image:: /_static/automation/execution/create_task.png
   :alt: Schedule from view
   :align: center

Tasks can be paused and resumed. Active tasks display the date that they will next be run by the scheduler,
as well as the amount of time left until then. Newly created tasks are set to pause by default.

Targets and payload
*******************

When creating a task, you can select a list of devices and pools. If these fields are left empty, the service will run on its own targets.
Otherwise, the task targets (all selected devices, plus all devices of all selected pools) will override the service targets when the service runs.
A task can also have a payload (dictionary) that will be passed to the service when it runs.

Syslog-triggered automation
---------------------------

eNMS can be configured to receive Syslog messages, and run a service upon receiving a message that
matches a particular pattern.

From :guilabel:`Scheduling / Events`, you can create these pattern-matching rules:

.. image:: /_static/automation/logs/log_rule_creation.png
   :alt: Creation of a log rule
   :align: center

A rule is defined by the following properties,
  - Name
  - Source IP: the IP address of the source.
  - Content: the content of the log.
  - Service: which service is triggered when the rule is matched by an incoming log.

For an incoming Syslog message to match the rule, both the "Source IP" and "Content" fields must match.
The match can be configured to be a regular expression.

.. note:: When a field is left blank, it is considered a match.
