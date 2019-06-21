====================
Log-based automation
====================

eNMS can be configured to act as a Syslog server, allowing for event-driven automation.
From the :guilabel:`logs/log_automation` page, you can define "log rules":

.. image:: /_static/automation/logs/log_rule_creation.png
   :alt: Creation of a log rule
   :align: center

A log rule is defined by the following properties:
    - Name of the rule.
    - Source IP: the IP address of the source, used to match a log received by eNMS against the log rule. This can also be a regular expression.
    - Content: the content of the log, used to match a log received by eNMS against the log rule. This can also be a regular expression.
    - Jobs: which services and workflows are triggered by eNMS when the rule is matched by an incoming log. A single log rule can have multiple jobs: they will be triggered sequentially by eNMS.

For an incoming Syslog message to match the rule, both the "Source IP" and "Content" fields must match.

.. note:: When a field is left blank, it is considered a match.

All log rules are listed in a table in :guilabel:`logs/log_automation`:

.. image:: /_static/automation/logs/log_rule_table.png
   :alt: Log Rule table
   :align: center

Whenever a log triggers a log rule, it is saved by eNMS in a separate table in :guilabel:`logs/log_management`.
