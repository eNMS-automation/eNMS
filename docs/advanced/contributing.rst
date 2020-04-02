.. _contributing:

============
Contributing
============

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
 flake8 --config tests/linting/.flake8 .

 # your code is mypy compliant
 # Mypy is a adds static type hinting to Python for the whole project; see (http://mypy-lang.org/)
 mypy --config-file tests/linting/mypy.ini .

 # your code is prettier compliant (javascript)
 npm run prettier

 # your code is eslint compliant (javascript)
 npm run lint
 
 # all the tests are passing
 pytest

If one of these checks fails, so will Travis CI after opening the pull request.

The CI/CD and PR processes are the same, because when you open a PR, this automatically triggers Travis.

If you are updating the documentation, you can build a local version of the docs:

::

 # build a local version of the docs
 cd /docs
 make html
