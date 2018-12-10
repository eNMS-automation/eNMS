=================
Role-based access
=================

When you create a new user from the :guilabel:`admin / User Management` page, you get to specify what the user can and cannot do.

.. image:: /_static/administration/user_creation_modal.png
   :alt: User creation
   :align: center

There are different types of access-rights:
    - Admin: Can do all admin-related tasks such as creating users, migrating the database, etc.
    - Connect: Can use the web SSH system to connect to devices.
    - View: Can access all pages in eNMS, but cannot edit anything, run a service/workflow, or connect to devices.
    - Edit: Can edit any type of object, except users.

By default, a user that does not have any right will only be able to access the dashboard.