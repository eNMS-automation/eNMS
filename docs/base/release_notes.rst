=============
Release Notes
=============

Version 3.18
------------

- Add Operational Data mechanism
- Removed Clusterized and 3D View
- Changed configuration to be a .json file instead of env variables
- Removed Custom config and PATH_CUSTOM_CONFIG
- Remove Configuration comparison mechanism
- Display the results of a workflow as a tree
- Change the mechanism to add a service to a workflow to be a tree
- Add the forward and backward control to the service managemet table.
- Duplicate button at workflow level to duplicate any workflow as top-level workflow
- Update to the operational data backup service to include rancid-like prefixes
- Add new "run method" property to define how a service is running (once per device, or once for all devices),
  and the equivalent property for workflow: run device by device, or service by service.
- Replace endtime with "duration" in the results and run table
- Fix bug infinite loop when adding a workflow to itself
- New "run method" option for services: : 
  - once per device
  - once for all devices
- New "run method" option for workflow
  - run device by device
  - service by service with workflow targets
  - service by service with service targets

Version 3.17.2
--------------

- Add Operational Data mechanism
- Removed Clusterized and 3D View
- Changed configuration to be a .json file instead of env variables
- Removed Custom config and PATH_CUSTOM_CONFIG
- Remove Configuration comparison mechanism

Version 3.17.1
--------------

- Performance optimization

Version 3.17
------------

- Performance improvements
- Refactoring of the result window
- Refactoring of the search system
- Forbid single and double-quotes in names.
- Moved the validation mechanism to the base "Service" class. Validation is now
  available for all services.
- New "Close connection" option for a service. Closes cached connection.
- In the "Advanced search", new "None" entry for filtering relationship.
- Removed mypy from both the codebase and CI/CD test (travis).
- Refactoring of the configuration management system.
- Refactoring of the workflow system
- Ability to specify the alignment for workflow labels
- Upon creating the admin user, check if there is a password in the Vault. If there isn't, create it ("admin").
- Remove beginning and trailing white space Names (service name ends with space breaks get_results)
- Add config mode and honor it when retrieving a cached connection.
- Netmiko Validation Service: allow several commands

Version 3.16.3
--------------

- If the admin password is not set (db or Vault) when creating the admin user, set it regardless of the config mode.
- Move skip / unskip button to right-click menu.

Version 3.16.2
--------------

- Always delete a workflow when it is imported via import job
- New "Maximum number of runs" property for a job in a workflow: defines how many times the same
  job is allowed to run in the workflow.
- New "Result postprocessing" feature: allows for postprocessing the results of a service
  (per device if there are devices), including changing the success value.
- Add new version of Unix Shell Script service
- Enable multiple selection in the workflow builder + mass skip / unskip buttons

Version 3.16.1
--------------

- New feature to stop a workflow while it's running

Version 3.16
------------

Re-add "Workflow Restartability" window when clicking on a job.

Cascade deletion of runs and results when jobs / devices are deleted.

change env variables name:

ENMS_CONFIG_MODE -> CONFIG_MODE
ENMS_LOG_LEVEL -> LOG_LEVEL
ENMS_SERVER_ADDR -> SERVER_ADDR
ENMS_DATABASE_URL -> DATABASE_URL
ENMS_SECRET_KEY -> SECRET_KEY
Make restart system work with get_result

Forbid empty names and names with slash front-end

Fix event issue after adding jobs to the workflow builder.

Create and delete iteration loopback edge upon editing the service.

Fix change of name in workflow builder upon editing the service.

Make iteration variable name configurable
Iteration value accesssed with get_var.

Ansible add exit status:

Workflow notes Desc: Support textboxes added to a workflow that are displayed in the workflow builder.

New mechanism: success as a python query kind of thingAdd success query mechanism

The "has device targets" property now defaults to True.

New Mechanism to switch back and forth in the workflow builder.

New "Latest runtime" optio in workflow builder (this is the default option).
When displaying a workflow, automatically jump to the latest runtime.

In Workflow builder, add the name of the user who ran the runtime in the runtime list.

Display number of runs in parallel in the Service Management / Workflow Management page, next to the Status (Running / Idle)

Job now displayed in grey if skip job is activated.

Edge labels are now editable

Results display: in text mode, multiline strings are now displayed without any transformation.

User inactivity monitoring

