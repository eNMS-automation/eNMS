=========
Execution
=========

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

Instead of running services immediately, they can be scheduled by creating a Task,
from the :guilabel:`Scheduling / Tasks` page.

You need to:

- Choose a name.
- Choose a scheduling mode: standard (start date / end date / frequency) or CRON.
- Select the service that you want to execute.
- Select a type of scheduling:
  - Standard scheduling: choose a start date and optionally, choose a frequency
    and an end date. If a ``Frequency`` is defined, the service will run periodically, in which case you
    can also choose an ``End date`` if you want the task to automatically stop running.
  - Cron scheduling: enter a crontab expression.

.. image:: /_static/automation/execution/create_task.png
   :alt: Schedule from view
   :align: center

Tasks are displayed in a table where they can be edited, duplicated, deleted, paused and resumed.
Active tasks display the date that they will next be run by the Scheduler, as well as the amount of time
until the next run.

.. image:: /_static/automation/execution/task_management.png
   :alt: Task management
   :align: center

Also, newly created tasks are set to Paused by default unless the 'Schedule task' checkbox is selected in the Create Task panel.

.. note:: 

  Crontab expression consists of a string of five numbers:  A  B  C  D  E   where:

  - A is minute 0-59
  - B is hour 0-23
  - C is day of the month 1-31
  - D is month 1-12
  - E is day of the week 0-6 (Sunday to Saturday)

  and where any of the fields can be defaulted to any with wildcard '*', and there are some extra special characters for defining repetition (see reference).

.. note:: Examples of crontab expressions:

  - ``*/5 1-2 * * *``   every 5 minutes between the hours of 1:00 and 2:00 am
  - ``*/1 * * * *``     every minute
  - ``30 4 1 * 0,6``	at 4:30 on the 1st day of every month, plus on Sun and Sat
  - ``00,30 * * * *``   at 00 and 30 minutes past every hour
  - ``30 9 * * * *``    at 9:30 am every day

Targets and payload
*******************

When creating a task, you can select a list of devices and pools. If these fields are left empty, the service will run on its own targets.
Otherwise, the task targets (all selected devices, plus all devices of all selected pools) will override the service targets when the service runs.
A task can also have a payload (dictionary) that will be passed to the service when it runs.

Syslog-triggered automation
---------------------------

eNMS can be configured to receive Syslog, and run services upon receiving Syslog messages matching a user-defined pattern.

From :guilabel:`Events`, you can define "log rules":

.. image:: /_static/automation/logs/log_rule_creation.png
   :alt: Creation of a log rule
   :align: center

A log rule is defined by the following properties:
    - Name of the rule.
    - Source IP: the IP address of the source, used to match a log received by eNMS against the log rule. This can also be a regular expression.
    - Content: the content of the log, used to match a log received by eNMS against the log rule. This can also be a regular expression.
    - Services: which services and workflows are triggered by eNMS when the rule is matched by an incoming log. A single log rule can have multiple services: they will be triggered sequentially by eNMS.

For an incoming Syslog message to match the rule, both the "Source IP" and "Content" fields must match.

.. note:: When a field is left blank, it is considered a match.

All log rules are listed in a table in :guilabel:`logs/log_automation`:

.. image:: /_static/automation/logs/log_rule_table.png
   :alt: Log Rule table
   :align: center

Whenever a log triggers a log rule, it is saved by eNMS in a separate table in :guilabel:`logs/log_management`.
