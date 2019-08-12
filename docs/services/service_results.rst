==============
Service result
==============

Service results
---------------

Real-time status update
***********************



Results are stored for each run of the Service Instance (and for Workflows at large).
The results are displayed as a JSON object. If the job ran on several device, you can display the results for a
specific device, or display the list of all "failed" / "success" device.
In the event that retries are configured, the Logs dictionary will contain an overall results section,
as well as a section for each attempt, where failed and retried devices are shown in subsequent sections
starting with attempt2.

You can compare two versions of the logs from the ``Logs`` window (a line-by-line diff is generated).
Here's a comparison of a ``Napalm get_facts`` service:

.. image:: /_static/services/service_system/service_compare_logs.png
   :alt: Compare logs
   :align: center

Service notification
--------------------

When a service (or a workflow) finishes, you can choose to receive a notification that contains the logs of the service (whether it was successful or not for each device, etc).

There are three types of notification:

- Mail notification: eNMS sends a mail to an address of your choice.
- Slack notification: eNMS sends a message to a channel of your choice.
- Mattermost notification: same as Slack, with Mattermost.

To set up the mail system, you must export the following environment variables before starting eNMS:

::

  MAIL_SERVER = environ.get('MAIL_SERVER', 'smtp.googlemail.com')
  MAIL_PORT = int(environ.get('MAIL_PORT', '587'))
  MAIL_USE_TLS = int(environ.get('MAIL_USE_TLS', True))
  MAIL_USERNAME = environ.get('MAIL_USERNAME')
  MAIL_PASSWORD = environ.get('MAIL_PASSWORD')

From the :guilabel:`Admin / Administration` panel, you must configure the sender and recipient addresses of the mail (Mail notification), as well as an Incoming webhook URL and channel for the Mattermost/Slack notifications.

.. image:: /_static/services/service_system/notifications.png
   :alt: Notification
   :align: center

The ``Mail Recipients`` parameter must be set for the mail system to work; the `Admin / Administration` panel parameter can
also be overriden from Step2 of the Service Instance and Workflow configuration panels. For Mail notification, there is
also an option in the Service Instance configuration to display only failed objects in the email summary versus seeing a
list of all passed and failed objects.

In Mattermost, if the ``Mattermost Channel`` is not set, the default ``Town Square`` will be used.

Gitlab Export
-------------

In the :guilabel:`admin/administration` page, you can configure a remote Git repository with the property ``Git Repository Automation``. Each service has a ``Push to Git`` option to push the results of the service to this remote repository.
This allows comparing the results of a service between any two runs.