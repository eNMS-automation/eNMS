==============
Run Management
==============

Run a job (service or workflow)
-------------------------------

You can run a job from:

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

Parameters
**********

- "Send notification" (boolean)
- "Notification Method": choose among mail, slack or mattermost.
- "Notification header": will be displayed at the beginning of the notification.
- "Include Result Link in summary": whether the notification contains a link to the results.
- "Mail recipients": if left empty, the recipients defined in the administration panel will be used.
- "Display only failed nodes": the notification will not include devices for which the job ran successfully.
