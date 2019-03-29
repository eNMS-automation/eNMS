.. _contributing:

============
Contributing
============

Contributions are welcome. If you want to contribute, you should join the #enms channel in the networktocode slack (http://networktocode.herokuapp.com/).

For developers
--------------

eNMS uses flake8 to make sure that the python code is PEP8-compliant, eslint to make sure the javascript code is compliant with google standards for javascript, and pytest for the test suite.
There is a dedicated ``requirements_dev.txt`` file to install these libraries:

::

 pip install -r requirements_dev.txt

Before opening a pull request with your changes, you should make sure that:

::

 # your code is PEP8 (flake8) compliant (python)
 flake8

 # your code is eslint compliant (javascript)
 eslint .

 # your code is mypy compliant (type hints)
 mypy .
 
 # all the tests are passing
 pytest

If one of these checks fails, so will Travis CI after opening the pull request.

The CI/CD and PR processes are the same, because when you open a PR, this automatically triggers Travis.
Both Black and Mypy are part of the eNMS CI/CD process. Black is a code formatting enforcement tool; see (https://github.com/ambv/black). And Mypy is a adds static type hinting to Python for the whole project; see (http://mypy-lang.org/).
Pre-commit is included in the dev requirements, and a pre-commit hook for black exists, so that each time you commit, it fails if the commit is not black-compliant, AND it automatically reformats your code to be black-compliant (and then you have to recommit).

If you are updating the documentation, you can build a local version of the docs:

::

 # build a local version of the docs
 cd /docs
 make html

=============
CLI interface
=============

eNMS has a CLI interface available for developers, with the following operations:

Fetch an object from the database
----------------------------------

General syntax: `flask fetch object_type object_name`
Example: `flask fetch device Washington`

Modify the properties of an object
----------------------------------

General syntax: `flask update object type 'object_properties'` where `object_properties` is a JSON dictionary that contains the name of the object, and the property to update. 
Example: `flask update device '{"name": "Aserver", "description": "test"}'`

Delete an object from the database
----------------------------------

General syntax: `flask delete object_type object_name`
Example: `flask delete device Washington`

Run a service
-------------

General syntax: `flask start service_name --devices list_of_devices --payload 'payload'` where:
- list_of_devices is a list of device name separated by commas.
- payload is a JSON dictionary.
Both devices and payload are optional parameters.

Example: `flask start get_facts`
Example 2: `flask start get_facts --devices Washington,Denver`
Example 3: `flask start a_service --payload '{"a": "b"}'`
Example 4: `flask start get_facts --devices Washington,Denver --payload '{"a": "b"}'`

==========================
Start eNMS in develop mode
==========================

By default, the `flask run` command with `FLASK_DEBUG` set to 1 will automatically reload the Flask app whenever a change is detected in the code.
However, because services are loaded programatically by eNMS, they are not being monitored by Flask and a change to a service will not trigger the application reload.
The `flask develop` is an improvement of the `flask run` command that adds all custom services to the list of files Flask monitors, so that any change to a service triggers a reload of the application.
It is recommended for people developing services.
