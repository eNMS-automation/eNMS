=============
Send a script
=============

Sending a script is done from the graphical view of the network, in two steps:
    
1. Selecting the target devices
#. Scheduling the script

Target selection
----------------

To select the targets, you must press ``Shift + Left-click`` and draw a selection rectangle that contains all targets.
All selected devices will be highlighted in red. Pressing ``Right-click`` will automatically unselect all devices.

.. image:: /_static/automation/send/target_selection.png
   :alt: test
   :align: center

Send the script
---------------

The geographical and logical views have an ``Automation`` drop-down list with all different types of script.
After the target devices have been selected, choose which type of script you wish to send.

.. image:: /_static/automation/send/choose_type.png
   :alt: test
   :align: center

Parameters
**********

The first step of the process is to choose a script, and configure specific per-task parameters.
Parameters depend on the type of script you want to send.

.. image:: /_static/automation/send/parameters.png
   :alt: test
   :align: center

Scheduling
**********

A script can be scheduled to run at a specific time, once or periodically (by filling the ``Frequency`` field (seconds)).
For a periodic script, an ``End date`` can be scheduled for the script to stop running automatically.
If the ``Start date`` field is left empty, the script will run immediately.

.. image:: /_static/automation/send/scheduling.png
   :alt: test
   :align: center