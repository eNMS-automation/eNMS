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

Fetching objects from the database
----------------------------------

General syntax: `flask fetch object_type object_name`
Example: `flask fetch device Washington`



