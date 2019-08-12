==============
Python objects
==============

There are a number of places in eNMS where the user is allowed to use pure python code:

- Inside double curved brackets in the service parameters (``{{ python code }}``). This is called "Variable substitution".
- In the ``Python Query`` field of the "Devices" section of a job. This field lets the user define the targets of a job programmatically.

