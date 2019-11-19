===============
Task Management
===============

In the previous section on Automation, the user could choose to run Services and Workflows immediately
from their respective menus. Such an execution is performed without the help of the Scheduler
and is simply a forked child process of eNMS.
Alternatively, Services and Workflows can be scheduled by creating a Task,
from the :guilabel:`scheduling/task_management` page.
The task is then handed-off to the scheduler for managing its execution.

Services and Workflows can be scheduled by creating a ``Task``, from the :guilabel:`Scheduling / Tasks` page.

You need to:

- Choose a name.
- Choose a scheduling mode: standard (start date / end date / frequency) or CRON.
- Select a service (the service or workflow that you want to execute).
    - If "Standard scheduling" was selected, choose a start date and optionally, choose a frequency and an end date. If a ``Frequency`` is defined, the service will run periodically, in which case you can also choose an ``End date`` if you want the task to automatically stop running. If you define a frequency but no ``End date``.
    - If "Cron scheduling" was selected, enter a cron expression.

.. image:: /_static/events/create_task.png
   :alt: Schedule from view
   :align: center

Task management
---------------

In the :guilabel:`scheduling/task_management` page, you can find a summary of all existing tasks.

Tasks can be:

- Created
- Edited
- Duplicated
- Deleted
- Paused and Resumed

Active/Resumed tasks display the time that they will next be run by the Scheduler, as well as the amount of time until the next run.

.. image:: /_static/events/task_management.png
   :alt: Task management
   :align: center

When creating a task, choose between:

- Standard Scheduling: has a recurring frequency (in seconds) and optional Start and Stop dates
- Crontab Scheduling: uses a crontab expression to specify when the task will be run. Refer to <a href=https://en.wikipedia.org/wiki/Cron>https://en.wikipedia.org/wiki/Cron</a> for explanation of crontab expression.

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
