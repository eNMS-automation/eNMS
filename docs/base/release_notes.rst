=============
Release Notes
=============

Version 3.20.2
--------------

- Keep selected runtime when entering a subworkflow.
- When running a workflow, add runtime to runtime list in workflow builder and select it.
- Workflow Refresh button now updates the list in the runtime dropdown.
- Create dedicated category for shared services in "Add services to workflow" tree.
- Implement "Clear all filters" mechanism for all tables
- When display workflow services in service table, all search input resetted (otherwise nothing was displayed)
- Add download buttons for configuration and operational data
- Add button in all tables to export search result as CSV file.

Version 3.20.1
--------------

- Update Generic File Transfer Service
- Fix runtime display bug in results window
- Fix file download and parameterized run bugs.
- Refactor LDAP authentication
- LDAP as first option if the LDAP authentication is active in settings
- Fix timing issue in SSH Desktop session mechanism
- Remove unique constraint for link names.
- Hash user passwords with argon2 by default. Add option to not hash user passwords in settings.
- Move linting and requirements in dedicated /build folder.
- Renamed key "pool" with "filtering" in properties.json
- Fix Service table filtering
- Fix object filtering from the network visualization page
- Fix Ansible service safe command bug and add regression test
- Remove column ordering for association proxy and all columns where ordering isn't useful
- Fixed workflow builder display when the path stored in local storage no longer exists
- Add service column in device results table
- Add result log deletion endpoint in RBAC
- Fix bug dictionary displayed in the UI in the results
- Add all service reference in submenu in workflow builder
- Add entry to copy service name as reference.
- Add new feature to accept a dictionary in iteration values. When a dictionary is used, the keys are used as the 
name of the iteration step in the results.
- Iteration variable are now referred to as global variable,
- Catch all exceptions in rest api to return proper error 500 (device not found for get configuration, etc)
- Fix bug position of shared services resetted after renaming workflow
- Fix refresh issue in configuration / operational data panel
- Fix upload of files from file management panel
- Forbid sets in the initial payload
- Fix user authentication when running a service
- Fix filtering tooltip in result table (no target found)
- Fix filtering per result type (success / failure) in result table
- Fix retry numbering
- Add Search REST endpoint

MIGRATION:
All iteration variable became GLOBAL VARIABLE, which means that you need to use
{{variable}} instead of {{get_var("variable")}} previously
All services that use iteration variables must be updated in the migration files.

Version 3.20
------------

- Add configuration management mechanism
- New Table properties mechanism: all table properties are displayed in a JSON file: you can configure which ones
appear in each table by default, whether they are searchable or not, etc, their label in the UI, etc.
You will need to add your CUSTOM properties to that file if you want them to appear in the table.
- Same with dashboard properties and pool properties
- New Column visibility feature
- New Configuration Management Mechanism
- RBAC
- Refactoring of the search system: next to the input, old "Advanced Search" button now dedicated
to relationship. Everything is now persisted in the DOM.

MIGRATION:
- In netmiko configuration backup service, rename:
  * "configuration" -> "configuration_command"
  * "operational_data" -> "operational_data_command"
- Moved ansible, pyats to a dedicated file called "requirements_optional.txt":

Version 3.19
------------

- Add new File Management mechanism: browse, download, upload, delete and rename local files.
  Mechanism to use local files as part of the automation services.
- Add new color code for the logs window.
- Add New Copy to clipboard mechanism:

    - copy from RC on a service in Workflow builder
    - copy from icon in result tables
    - copy dict path to result in the json window.

- Full screen workflow builder
- Remember menu size PER USER
- Refactoring of all the tables
- Refactoring of the top-level menu
- Alerts are saved and displayed in the UI, top menubar.
- Remove recipients from settings.json. Recipients is now a mandatory field if mail notification is ticked.
- Add support for netmiko genie / pyATS (`use_genie`) option.
- New "Desktop session" mechanism to SSH to a device using teraterm / putty / etc.

MIGRATION:
- Renaming "config" -> "settings". All services that use the "config" global variable must change it to "settings".
- Session change log: some traceback previously returned as "result" key of service "results" now returned as "error":
can create backward-compatibility issue when a workflow relies on the content of the traceback.

Version 3.18.2
--------------

- Fix subworkflow iteration bug
- Fix workflow display with same shared services in multiple subworkflows
- Fix task / run cascade deletion bug on MySQL
- Add "devices" keyword for result postprocessing
- Allow restart from top-level workflow when restarting from a subworkflow service
- New "Skip value" property to decide whether skip means success or failure
- Fix the workflow builder progress display when devices are skipped. Now eNMS shows how many devices
are skipped, and it no longer shows anything when it's 0 ("0 failed", "0 passed" etc are no longer displayed)
- Netmiko session log code improvement for netmiko validation / prompt service

Version 3.18.1
--------------

- Display scoped name in hierarchial display mode
- Fix bug "Invalid post request" editing edge
- Improve display of filtering forms
- Reduce size of the service and workflow edit panel for low-resolution screens
- Add "success" key before result postprocessing
- Remove "Enter subworfklow" button in toolbar and add the same button in right-click menu
- Add button to switch to parent workflow

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

- Add "Workflow Restartability" window when clicking on a job.
- Cascade deletion of runs and results when jobs / devices are deleted.
- Forbid empty names and names with slash front-end
- Fix event issue after adding jobs to the workflow builder.
- Create and delete iteration loopback edge upon editing the service.
- Fix change of name in workflow builder upon editing the service.
- Make iteration variable name configurable
- Ansible add exit status:
- Workflow notes Desc: Support textboxes added to a workflow that are displayed in the workflow builder.
- New mechanism: success as a python query kind of thingAdd success query mechanism
- New Mechanism to switch back and forth in the workflow builder.
- New "Latest runtime" option in workflow builder.
- When displaying a workflow, automatically jump to the latest runtime.
- In Workflow builder, add the name of the user who ran the runtime in the runtime list.
- Display number of runs in parallel in the Service Management / Workflow Management page,
  next to the Status (Running / Idle)
- Job now displayed in grey if skip job is activated.
- Edge labels are now editable
- Results display: in text mode, multiline strings are now displayed without any transformation.
- User inactivity monitoring

Version 3.15.3
--------------

- "Use Workflow Targets" is now "Device Targets Run Mode"
- Service mode: run a workflow service by service, using the workflow targets
  Device mode: run a workflow device by device, using the workflow targets
  Use Service targets: ignore workflow targets and use service targets instead

Version 3.15.2
--------------

- New "Iteration Targets" feature to replace the iteration service
- Front-end validation of all fields accepting a python query
- check for substitution brackets ({{ }}) that the expression is valid with ast.parse
- Add new regression test for the payload extraction and validation services
- Payload extration refactoring

  - Store variables in the payload global variable namespace
  - Add optional operation parameter for each variable: set / append / extend / update

- New conversion option: "none" in case no conversion is necessary
- No longer retrieve device configuration when querying REST API.
- Remove web assets
- Refactor SQL Alchemy column declaration for MySQL compatibility
- Hide password in Ansible service results.
- Private properties are no longer considered for pools.

Version 3.15.1
--------------

- Waiting time is now skipped when the job is skipped.
- Change result to mediumblob pickletype
- remove Configurations from ansible command
- remove table filtering N/A
- Add more regression tests (including skip job feature)

Version 3.15
------------

- New env variable: CUSTOM_CODE_PATH to define a path to a folder that contains custom code that
  you can use in your custom services.
- Advanced search: per relationship system
- eNMS version now displayed in the UI. The version number is read from the package.json file.
- Real-time log mechanism with multiprocessing enabled.
- Workflow restartability improvement:
- Fixed bug in tables: jump to bottom after page 1 when table is refreshed.
- Fixed panel repaint bug when pulling it down.
- Relationship are now displayed in the edit window: you can edit which service/workflow a device/task is a target of, etc...
- Spinning GIF when AJAX requests
- Add new services in a workflow: services are spread in a stairsteps in the workflow builder.
- Workflow Builder: edit the service when it's double clicked
- Copy to clipboard for device configuration
- Fix bug subworkflow edit panel
- Export Jobs needs to automatically delete devices and pools
- Service should fail if a python query produces a device target that does not match inventory/database
- timeout and other parameters getting updated for all services using cached Netmiko connections.
- Ability to close a cached connection and re-originate the connection in a service.
- Start time of each Service within a Workflow displayed,
- User can now track the progress of a workflow even if the workflow was started with a REST call
- New GET Result Endpoint for the REST API to get the result of a job run asynchronously:
  if async run_job was invoked, you can use the runtime returned in the REST response to collect the results
  after completion via a GET request to /result/name/runtime
- New Run Management window:
- Slashes are now forbidden from services and worklfow names (conflict with Unix path)
- The command sent to a device is now displayed in the results
- Credentials are now hidden when using gotty.
- Job Parametrization.
- Service type now displayed in the workflow builder.
- New service parameter: Skip (boolean)
- New parameter: Skip query (string) Same as skip, except that it takes a python query.
- Added number of successful / failed devices on workflow edges.
- Run status automatically switched from "Running" to "Aborted" upon reloading the app.
- napalm getter service: default dict match mode becomes inclusion.
- Replaced pyyaml with ruamel
- Both true and True are now accepted when saving a dictionary field.
- Set stdout_callback = json in ansible config to get a json output by default.
- Change in the LDAP authentication: LDAP users that are not admin should now longer be allowed to log in (403 error).
- The "dictionary match" mechanism now supports lists.
- New "Logs" window to see the different logs of a service/workflow for each runtime.
- Show the user that initiated the job, along with the runtime when selecting a run
