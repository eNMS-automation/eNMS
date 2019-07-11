.. _contributing:

============
Contributing
============

Contributions are welcome. If you want to contribute, you can join the #enms channel in the networktocode slack (http://networktocode.herokuapp.com/).

For developers
--------------

eNMS uses :

- Black for python code formatting
- Flake8 to make sure that the python code is PEP8-compliant
- Mypy for python static type hinting
- Prettier for javascript code formatting
- Eslint to make sure the javascript code is compliant with google standards for javascript
- Pytest for the test suite.

There is a dedicated ``requirements_dev.txt`` file to install these python libraries:

::

 pip install -r requirements_dev.txt

Before opening a pull request with your changes, you should make sure that:

::

 # your code is black compliant
 # Black is a code formatting enforcement tool; see (https://github.com/ambv/black)
 black --check --verbose .

 # your code is PEP8 (flake8) compliant (python)
 flake8 --config linting/.flake8 .

 # your code is mypy compliant
 # Mypy is a adds static type hinting to Python for the whole project; see (http://mypy-lang.org/)
 mypy --config-file linting/mypy.ini .

 # your code is prettier compliant (javascript)
 npm run prettier

 # your code is eslint compliant (javascript)
 npm run lint
 
 # all the tests are passing
 pytest

If one of these checks fails, so will Travis CI after opening the pull request.

The CI/CD and PR processes are the same, because when you open a PR, this automatically triggers Travis.
Pre-commit is included in the dev requirements, and a pre-commit hook is available, so that each time you commit, it fails if the commit is not black-compliant AND flake8-compliant, AND it automatically reformats your code to be black-compliant (and then you have to recommit).

If you are updating the documentation, you can build a local version of the docs:

::

 # build a local version of the docs
 cd /docs
 make html

eNMS architecture
-----------------

eNMS architecture follows the Model - View - Controller pattern (MVC).

The view is the GUI. It relies on:
- HTML templates with the Jinja2 template engine, located in eNMS/templates
- JavaScript. The JavaScript code is located in eNMS/static.
Switching from one page to another page in the eNMS menu results in a GET request, everything else is an AJAX POST request.
- wtforms, a python library to define form (properties of the form and type of property), as well as validate them. All forms are in eNMS/forms.

The Controller is located in eNMS/controller. It defines what needs to be done whenever a POST request is received.
In most web project (no matter what framework is used: Flask, Django, etc), the application logic and the framework are entangled in "routes". eNMS is built around the idea that the application logic and the framework should be completely decoupled.
Flask is used in eNMS as nothing more than an HTTP router and a session management library. Flask routes are all contained in eNMS/routes.py. There is a single route for all POST requests. This route redirects the request to the appropriate function of the controller.
The advantage of this design is that, if the need ever arises to move away from Flask to another web framework, there is very little to be done.

The "Model" is based on SQL Alchemy. Althought there is a library called "flask_sqlalchemy" to ease the integration of Flask and SQL Alchemy, it is not used in eNMS on purpose, for the reason mentioned above and generally to have the least possible interdependency among requirements.
All models are contained in eNMS/models.

The models, controller, and forms are all separated in different "categories":
- Administration: user management, database migration and deletion, import and export of the topology, etc.
- Inventory: devices, links, pools, and configuration management.
- Automation: services, workflow, workflow management.
- Scheduling: task, calendar, and events (event-driven automation).
This separation is reflected in the GUI as well as in the code, each section having a separate menu.

eNMS uses metaclasses and SQL Alchemy events to understand the model, by inspecting an object definition at creation time.
- Forms have a metaform in eNMS/forms/__init__.
- Models are inspected by the SQL Alchemy "mapper_configured" event, in eNMS/database/events.py

