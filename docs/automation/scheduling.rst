==========
Scheduling
==========

Tasks
-----

Creating Tasks
==============

Instead of running services immediately, they can be scheduled by creating a task, from :guilabel:`Scheduling / Tasks`.
You need to enter a name, which service you want the task to execute, and a scheduling mode.

There are two scheduling modes:

  - **Date Scheduling**: enter a start date and optionally a frequency and an end date.
    If a ``Frequency`` is defined without an end date, the service will keep running until manually stopped.
  - **Cron Scheduling**: enter a crontab expression
    - `Crontab format reference <https://en.wikipedia.org/wiki/Cron#Overview>`_
    - reminder::

      minute(0-59) hour(0-23) day-of-month(1-31) month(1-12) day-of-week(0-6)

  - Example - every 15 minutes on Tuesday and Thursday::

       */15 * * * 2,4

When creating a task, you can select a list of devices and pools. If these fields are left empty, the service will run on
its own targets. Otherwise, the task targets (all selected devices, plus all devices of all selected pools) will override the service
targets when the service runs.

A task can also have a payload (dictionary) that will be passed to the service when it runs.

Managing Tasks
==============

Newly created tasks are set to **paused** by default.  Tasks can be paused and resumed. Active tasks display the date that they will next be run by the scheduler,
as well as the amount of time left until then.

**Troubleshooting**: if a task is **Active** without a next run date, it is likely that
the scheduled job database was lost.   Try editing the Task and saving it.  This will restore the scheduled
portion of the Task.


Timezone Considerations
=======================

When specifying a start time, you must take into account the server's time zone configuration.  Normally, this is in UTC
(Coordinated Universal Time).   To run a scheduled task at a specific local time, the start time OR crontab expression will
need to be adjusted depending on the local time zone - and Daylight Savings Time if applicable:

  - Time zone conversion - CST/CDT

      - Central Time zone (CST) is UTC-6 (Fall back)
      - Central Daylight Time (CDT) is UTC-5  (Spring forward)

  - Example

      - Reporting service: every 8:00 AM on Monday/Wednesday/Friday
      - Crontab - hour value is either **13:00 or 14:00** depending on the time of the year! ::

         0 13 * * 1,3,5

Syslog-triggered automation
---------------------------

eNMS can be configured to receive Syslog messages, and run a service upon receiving a message that
matches a particular pattern.

From :guilabel:`Scheduling / Events`, you can create these pattern-matching rules.

A rule is defined by the following properties:

  - Name
  - Source IP: the IP address of the source.
  - Content: the content of the log.
  - Service: which service is triggered when the rule is matched by an incoming log.

For an incoming Syslog message to match the rule, both the "Source IP" and "Content" fields must match.
The match can be configured to be a regular expression.

.. note:: When a field is left blank, it is considered a match.
