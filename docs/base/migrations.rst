==========
Migrations
==========

Go to eNMS root folder and run "flask db upgrade"
-------------------------------------------------

Each major release of eNMS is packaged with an alembic migrations script that will perform schema translation of the database from the last major release of eNMS.

To run the migration script, run the following command:

::

 flask db upgrade
