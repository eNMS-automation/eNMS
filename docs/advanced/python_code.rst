===========
Python code
===========

There are a number of places in the GUI where the user is allowed to use pure python code:

- Inside double curved brackets in the service parameters (``{{python expression}}``). This is called "Variable substitution" (fields that support variable substitution are marked with a light blue background).
- In the ``Python Query`` field of the "Devices" section of a service. This field lets the user define the targets of a service programmatically.
- In the ``Skip Job If Python Query evaluates to True`` field of the "Workflow" section of a service. This field lets the user define whether or not a service should be skipped programmatically.
- In the ``Query`` field of the Variable Extraction Service.
- In the code of a Python Snippet Service.

You have access to the following variables:

- ``device``: current device, if the ``Has Device Targets`` is ticked ("device" object).
- ``payload``: current state of the workflow payload (dictionary).
- ``config``: eNMS global configuration (available in the administration panel, section "Parameters", button "General").
- ``workflow``: parent workflow, if the service is running within a workflow.
- ``workflow_device``: parent device, parent device, available only when device targets are defined using a Python Query.

And the following functions:

- ``get_var`` and ``set_var``: function to save data to and retrieve data from the payload.
    The use of these two functions is explained in the section ""Set and get data in a workflow" of the workflow payload docs.
- ``get_result``: function to retrieve a result for a given service (and for an optional device).
    The use of this function is described in the section "Use data from a previous service in the workflow" of the workflow payload docs.
