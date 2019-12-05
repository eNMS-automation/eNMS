==========
Scheduling
==========

Tasks
-----

Instead of running services immediately, they can be scheduled by creating a task, from :guilabel:`Scheduling / Tasks`.
You need to enter a name, which service you want the task to execute, and a scheduling mode.
There are two scheduling modes:
  - Date Scheduling: enter a start date and optionally a frequency and an end date.
    If a ``Frequency`` is defined without an end date, the service will keep running until manually stopped.
  - Cron Scheduling: enter a crontab expression.

Tasks can be paused and resumed. Active tasks display the date that they will next be run by the scheduler,
as well as the amount of time left until then. Newly created tasks are set to pause by default.


When creating a task, you can select a list of devices and pools. If these fields are left empty, the service will run on
its own targets.
Otherwise, the task targets (all selected devices, plus all devices of all selected pools) will override the service
targets when the service runs.
A task can also have a payload (dictionary) that will be passed to the service when it runs.

Syslog-triggered automation
---------------------------

eNMS can be configured to receive Syslog messages, and run a service upon receiving a message that
matches a particular pattern.

From :guilabel:`Scheduling / Events`, you can create these pattern-matching rules.

A rule is defined by the following properties,
  - Name
  - Source IP: the IP address of the source.
  - Content: the content of the log.
  - Service: which service is triggered when the rule is matched by an incoming log.

For an incoming Syslog message to match the rule, both the "Source IP" and "Content" fields must match.
The match can be configured to be a regular expression.

.. note:: When a field is left blank, it is considered a match.
