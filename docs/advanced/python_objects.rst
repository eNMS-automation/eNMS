===========
Python code
===========

There are a number of places in the GUI where the user is allowed to use pure python code:

- Inside double curved brackets in the service parameters (``{{ python code }}``). This is called "Variable substitution".
- In the ``Python Query`` field of the "Devices" section of a job. This field lets the user define the targets of a job programmatically.
- In the ``Skip Job If Python Query evaluates to True`` field of the "Workflow" section of a job. This field lets the user define whether or not a job should be skipped programmatically.
- In the ``Query`` field of the Variable Extraction Service.
- In the code of a Python Snippet Service.

You have access to the following variables:

- ``device``: current device, if the ``Has Device Targets`` is ticked ("Device" object).
- ``payload``: current state of the workflow payload (dictionary).
- ``config``: eNMS global configuration (available in the administration panel, section "Parameters", button "General").
- ``workflow``: parent workflow, if the service is running within a workflow.
- ``workflow_device``: parent device, if the device targets are defined programmatically based on the workflow device.

And the following functions:

- ``get_var`` and ``set_var``: function to save data to and retrieve data from the payload.
    The use of these two functions is explained in the section ""Set and get data in a workflow" of the workflow payload docs.
- ``get_result``: function to retrieve a result for a given job (and for an optional device).
    The use of this function is described in the section "Use data from a previous job in the workflow" of the workflow payload docs.
