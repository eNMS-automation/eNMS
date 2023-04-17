
# Release Notes


Version 4.5.0
-------------

- Bulk Filtering mechanism
  - refactoring of the service template with new Jinja2 macro
- Round result size to 1 decimal when the result size is higher than 50% the maximum
  allowed size
- Don't allow saving a workflow if the run method is set to Service x Service and the
  workflow has target devices or pools
- Don't allow skipping services in a workflow if workflow edit is restricted to
  owners via RBAC access control
- Remove all references to old "update_pools" mechanism (removed last release)
  Commit: 14e57286f731dcd5e8302abe327ef5d9d5c2dfbf
- Add new "no_search" keyword argument in SelectField and MultipleSelectField
  to disable search box (in service form)
- Remove `hash_user_passwords` options from settings.json (always hash passwords)
  Remove ability to use user passwords for automation & web SSH.
- Remove pin to 2.3.3 for wtforms in requirements
- Remove pin to 1.0.1 for flask_wtf in requirements
- Remove pin to 2.0.1 for itsdangerous in requirements
- Remove pin to 1.4.46 for sqlalchemy in requirements (move to sqlalchemy v2)
- Fix duplicated run name when running a service from the REST API bug
- Order model drop down lists in the UI based on pretty name instead of tablename
- Add user "last login" and "last request" properties
  Commit: f2e4f2658ae0157020412684226e2a1a8cb58aa2

Version 4.4.0: RBAC and Credentials
-----------------------------------

- Remove settings from UI upper menu (doesn't work with multiple gunicorn workers)
- Add post_update function (60350ede71f6a5146bab9f42a87f7fef0360b98e) after db flush in controller udpate function to compute pool only after the ID has been set, and
  determine what properties to return (e.g not serialized object but only what is needed)
  Return default serialized properties in controller update instead of all serialized relationship for scalability with > 50K devices.
- Refactor freeze edit / run mechanism (pure python check instead of SQL query with originals)
- New Bulk Edit option for appending / removing to a multiple instance list (dropdown list on the right of the field).
- Add regression tests for get_connection global variable
- New defaultRbac mechanism to set rbac value of filtering function. In the
  configuration table, the default RBAC mode is set to "configuration".
- Use tableOrdering function when initializing a table instead of redrawing table
  after initialization, to avoid calling draw function twice when loading a table.
  Commit: 7d8999d0fc4ac7a6a7fd49e3275fdca4ac12ade3
- Added "last_modified_by" property to store name of user who last modified
  service/object/pool
  Mail: "new feature request (minor)"
  Commit: 0e0d90aeac5f5a977e6a452946794cd1293621ed
- Added mechanism to update last_modified property of a workflow whenever there
  is any change to an (sub)edge or a (sub)service.
  Cases when the last modified property is updated:
  - the workflow itself is updated
  - any service or subservice is updated (ie including subworkflows)
  - copy service in workflow is used in workflow or subworkflows
  - add edge in workflow or subworkflows
  - any deletion is made in workflow or subworkflows
  - any service is skipped in workflow or subworkflows
- Same last_modified(_by) mechanism for devices, links and pools.
- Make buttons in path displayed in Files table clickable to move to button folder (#275).
- Refactor get function to fix scalability issues:
  - The properties sent to the front-end are defined in properties.json > "panel"
  - Remove get_all controller endpoint (unused)
  - Remove get_properties controller endpoint (replaced by get with "properties_only" keyword)
- In task form validation (#267):
  - Forbid end date to be equal or anterior to start date.
  - Forbid frequency to be 0 when a task has an end date (= is periodic)
- Fix URL encoding for links to workflow builder with runtime (encode space to %20) (#278)
- Add Clear Search button in file table
- Use SQL Alchemy `regexp_match` mechanism (new from 1.4, replaced eNMS custom per DB regex match mechanism)
  Link: https://docs.sqlalchemy.org/en/14/core/sqlelement.html#sqlalchemy.sql.expression.ColumnOperators.regexp_match
  Commit: a6af8a88f197b891928986dd492ce2ff39fc629a
- Add "creator" properties in all edit panels
- Fix link to workflow / network set to None after creating new or duplicating existing
  instance (via post_update mechanism)
- Fix asynchronous bug in netmiko services: wrong disabled status after opening
  edit panel to a service in netmiko "Expect String" field.
- Fix bug where RBAC Edit access is needed to run a service
  Thread: "Edit Service/Device Needed for user using /rest/run_service"
- Remove "settings" from global variables so that it cannot be overridden.
  Thread: "Settings and security question"
- Enable migration for files and folders.
- When selection in builder changed, close deletion panel (wrong node / edge count)
  Issue #280 / Commit 6fc007f6a1d43fd2b61652f02983dba0cedef68a
- Resize table headers when the panel that contains the table is resized
  Commit 40a909673f4b9cfbfcae58fb60e86f6e6bd83994
- When a file is deleted, mark as missing instead of deleting associate file object
- Make "update device RBAC" pool mechanism accessible from REST API.
- Fix bug where using run_service REST endpoint with non existing device returns 403
  not allowed error instead of more specific "Device not found" error
- Add new "Credential Object" mechanism in connection services, REST service and
  generic file transfer service. Choose credential object explicitly instead of using
  custom username / password.
- Report feature
  - Report template can use python substitution or Jinja 2
  - Report output can be either text-based or HTML
  - Option to display the report when the run is over instead of the service results.
  - Option to send report as part of the email notification
  - Report can be used for any services in a workflow, not just the workflow itself.
  - In get_result, new "all_matches" keyword to get all results.
  - New "files" / "reports" folder to store predefined templates that are used to
    populate the "report" field in the service edit panel.
  - Add new "get_all_results" function in the global variables
- Add support for distributed task queue for automation with Dramatiq.
- Return an error in the UI if the commit of workflow logs, report or result
  fails (e.g data too long db error because of payload data for the results),
  don't commit if the size of the data is higher than the maximum column size
  configured in database.json, and emit warning if it is than 50%
- Fix "List index out of range" bug in Jump on Connect mechanism
  Commit 457f46dd2c496757e924d922f3455626d35a3784
- Add RBAC support to credentials
- Fix Netmiko exit_config_mode bug (to be called after commit)
- Add new "log_events" key under settings.json > files to control whether file changes
  must be logged as unix log and changelog.
- Add new "Disable Workflow" feature:
  - New property "Disabled" in service form to disable a workflow
  - When a service / workflow is disabled, it cannot be run from the UI or the REST API
  - New property "Disabled Time & User": if the workflow is disabled, indicates when the
  service was disabled and by whom; empty otherwise.

RBAC Refactoring:
- Service export: owners and RBAC read / edit / etc are exported in the service
  .yaml file. If the importing user doesn't have access to the service based on
  how RBAC is set up, the service will not be visible after export.

Migration:
- The credential file must be updated to use groups instead of pools
  ("user_pools" -> "groups"). The appropriate groups must be created first.
- In migration files, check that the "settings" variable isn't used in
  any workflow. If the server IP, name or URL is used, the "server" variable
  should be used instead.
- "get_all" and "get_properties" controller functions have been removed.
  Check that they are not used anywhere in custom code (plugin, custom.py, etc)

Test (besides what is in release notes):
- the notification mechanism hasn't been impacted (in particular notification header
  option + devices results)
- Jump on connect mechanism
- RBAC
  - new mechanism
  - Freeze Edit / Run mechanism (refactored)

Version 4.3.0
-------------

- Remove 3D Geographical Visualization.
- Default to "info" for services log level. Move "Disable logging" at the end of the list.
- Add "username" variable in workflow global space set to the user that runs the workflow.
- Forbid deletion of Start, End and Placeholder services.
- Fix merge_update behavior to not extend list every time an object is edited.
- Define Server IP address and URL with the `SERVER_ADDR` (default `0.0.0.0`) and `SERVER_URL` (default `http://192.168.56.102`) environment variable instead of `settings.json` / `app` section (as VM
  settings, they don't belong in the application settings and shouldn't be checked in the code).
- Add new "server" variable in workflow global space set to a dictionary that contains server name,
  IP address and URL.
- Make "Results as List" False by default for scrapli (not useful when only
  one command, which is most of the time).
- For consistency with Scrapli
  * Rename "Netmiko Validation" to "Netmiko Commands"
  * Allow sending multiple commands via Netmiko Commands
  * Add "Results as List" to Netmiko Commands 
- Add "use genie" option in netmiko commands service for Genie / PyATS support
- Add Jinja2 template support for netmiko and scrapli commands field (iteration no longer required for loops).
- Add new `default_function` (sqlalchemy parameter) and `render_kw` (wtforms parameters) for custom fields in properties.json.
- Add new `rest/workers` GET endpoint to get service count + cpu / memory usage for each 
  WSGI worker (admin endpoint).
- Data Extraction Service update:
  * Rename to "Data Processing" service
  * Fix bug if no device (service in run once mode)
  * Add new option to parse TextFSM as JSON object
  * Add new option to support Jinja2 Template conversion
  * Add new option to support Template Text Parser conversion
- Fix bulk deletion and bulk removal from a filtered table (e.g dashboard bulk deletion deletes everything,
  not just the objects displayed in the table).
- New feature to align nodes in Network Builder and Workflow Builder:
  - Horizontal and vertical alignment
  - Horizontal and vertical distribution
- Make all objects in object select list (both single and multiple entries) hyperlink to the edit panel.
- Make all results in the Results table link to the workflow builder.
- Make it possible to share link to a specific workflow / runtime (optional) to the workflow builder,
  with the following syntax: workflow_builder/{workflow_id}/{runtime}.
- Add "shared" property to the service table.
- Add shared subworkflow to the list of top-level workflows in the workflow builder to provide
  the ability to view all runtimes (including when it was run as standalone workflow).
- Remove "Approved by admin" mechanism for Unix Command Service. Instead, check if the new command is
  different from the old command: if it is and the user is not an admin, an error is raised.
- Remove backward / forward mechanism in the network and service table. Make networks / workflows links to
  the network / workflow builder for consistency with results page.
- Add User Profile window to change username, password, user email, etc.
- Add User landing page to decide which page to display after logging in (editable in profile).
  Default landing page is configurable from settings.json > authentication > landing_page.
- Add mechanism to show a single device status in workflow builder UI (logs filtering + service display)
- Add mechanism to search for a string across all services of a workflow in the workflow builder, and
  across all nodes in the network builder.
- Fix vertical alignment in all tables (cell content was not centered on y axis because of buttons height in
  the last column).
- Add export service button in Workflow Builder.
- New Files Management System:
  * defined via settings / paths / files (default: eNMS / files folder)
  * files are automatically scanned when starting the application, and can be rescanned via the UI
  * files have a "Status" property showing the last action (updated, moved, deleted, etc)
  * last_modified is the unix last modified timestamp
  * files can be displayed hierarchically or flat in the table (default: hierarchical display)
  * both files and folder can be exported to browser; folders are compressed as tgz before export
  * new files can be uploaded to any folder from the UI
  * deleting a file or folder in eNMS will delete it locally
  * a folder can be created in currently displayed folder, not a file because a file must be
    associated with a local file.
  * watchdog is used to keep track of all files change done outside of the app
- redis config in settings.json moved to the inner key "redis" > "config
- redis new option in settings.json > "redis" > "flush_on_restart": flush redis queue when the app restarts.
- Remove check box for "use device driver" add "use device driver" into drop down and make this the default.
- Add get_connection function in global variables to access connection object from a python snippet service.
  A non-default connection can be retrieved from the cache by passing the keyword argument "name".
- Support custom ip address in ping service (new IP address field, defaults to device IP if empty).
- Add new "mandatory" keyword in custom properties to make the field required to submit the form.
- Add new "allow_password_change" keyword in settings > authentication to configure whether the user
  profile lets users change their own password (if `false`, the password field is not shown)
- Add new "force_authentication_method" to force users to log in with the authentication method saved in
  the database (e.g first authentication method used)
- Add new 'Man Minutes' feature to compute time saved per workflow
  * Only for top-level workflows
  * Man Minutes can be defined per device or for the whole workflow
  * Per Device is only allowed if the workflow run method is DxD or SxS with workflow targets
  * The workflow must be a success (or per device success) to be counted in the total man minutes
  * Man Minutes can be made mandatory via 'mandatory_man_minutes' key in automation.json > workflow
- Remove unused parent and parent_device relationship on the Run class.
- Import Services:
  * The timeout for the Import_services endpoint is configurable in "automation.json" under
    the "service_import" > "timeout" property. Logging on timeout is also improved.
  * The "stem" of the imported file (e.g., service.tgz) does not have to exactly match the
    directory in the .tgz file (i.e., "serviceA_v1.tgz" with "serviceA/service.yaml" is supported).
- The napalm ping service separated the `ping_timeout` from the napalm `timeout`.
- Add new settings "max_content_length" in settings.json > "app" (Flask parameter)
- Add new timeout setting for file import in settings.json > "files"

Migration
- check "username" and "server" variables in workflow aren't in conflict with existing workflows.
- dashboard is now controlled by RBAC: dashboard access must be explicitly granted via access pages, GET and
  POST requests.
- "download_file" endpoint -> "download" (add support for downloading folders)
- the "driver" property must be updated for all netmiko, napalm and scrapli via the migration script
- update services to use server IP and address from global variables and not from settings.
- the napalm_ping_service added a `ping_timeout` property. If desired, set both
  values to be at least the defaults (2 for `ping_timeout`, 10 for napalm's `timeout`)

To be tested:
- bulk deletion and bulk removal (from dashboard and other tables too)
- mail notification
- web ssh
- service logging mechanism, including disable logging
- netmiko commands service: test old services still work + new multi commands / results as list option

Version 4.2.0
-------------

- Add Network builder mechanism
- Add 3D visualization of network devices
- Extend Devices and Links with subclass / custom properties and a separate tab in the UI, the same way services work.
- Remove deep_services function used for export, use service.children relationship instead.
- Dont subclass SQLAlchemy Column following advice of SQLAlchemy creator.
- Make corrupted edges deletion mechanism a troublehooting snippet instead of a button in the admin panel.
- Move redis configuration in settings.json > "redis" key
- Add new mechanism to limit results in server-side drop-down list with filtering constraints.
- Limit superworkflow selection to workflows that contains the shared Placeholder service.
- Set trigger variable to "Regular Run" or "Parameterized Run" when service is triggered from the UI instead of "UI".
- Add SSH Proxy mechanism (multiple jump server in gateways property, gateway device subtype, priority
  tie-break mechanism)
- Consider runtime limiting user / all toggle mechanism in the restart service window.
- Move doc link to settings.json to allow custom doc links for plugins. Generate doc link in the jinja2 template
  instead of javascript (otherwise, wrong doc link until updated in js)
- Move tables refresh rate to settings.json to allow for custom refresh rates.
- New "Category" property / mechanism for the drop-down list of the site and workflow builder.
- Reinstate service selection with single left click (Ctrl no longer needed)
- Remove pytest, coverage, and travis dependencies.
- Reinstate single left click for node selection in workflow & site builder.
- Remove most union subquery in rbac_filter because a union of query yields a CompoundSelect
  SQLAlchemy object, and this is not compatible with using with_entites (via filtering properties kw).
- Fix export in bulk (the hierarchical display mode was not considered, all services inside a workflow
  were exported even when "hierarchical display" was selected)
- Add notification banner mechanism
- Remove default_access property, replace with "admin_only" boolean. Impact on migration.
- Make "run_service" rest api endpoint default to async True
- Update netmiko and napalm Backup services to load deferred row before updating. Impact on both services.
- Remove pathlib from requirements.txt
- Update workflow algorithm to not add services to priority queue in DxD mode if all are discarded.
- Update Ansible Service to use custom path in cwd argument of subprocess.check_output.
- Change default priority to 10 for services. Update of migration files required.
- Add new check box "Approved by an Admin user" in the Unix Command service. That box must be ticked by
  an admin user for the service to be allowed to run. A non-admin user cannot save a service if it is
  ticked, meaning that each time a Unix Command service is edited, it must be re-appproved.
- Add new timeout parameters for Scrapli service
- Always show security logs, even when logging is disabled. Add "allow_disable" (default: True) keyword argument
  to log function to prevent logs from being disabled if necessary.
- Add new 'deactivate_rbac_on_read' property in rbac.json, under 'advanced' key. Set to true by default.
  When true, eNMS no longer applies rbac for reading from the database. (=> better performances)
- Make the vendor, operating_system and model properties a custom list for devices, links and services,
  and category for sites and workflows. The drop-down list choices can be configured in properties.json > property_list key.
- Add support for renaming objects from the REST API (with key "new_name")
- Add limit to maximum number of nodes that can be displayed in site builder". Configurable via
  visualization.json > Network Builder > max_allowed_nodes
- Add new option to display site nodes as ellipses instead of images for better performances. Configurable via
  visualization.json > Network Builder > display_nodes_as_images
- Auto-update Vendor and Operating System property value of a new service in the workflow builder
  based on the values of these properties in the parent workflow.
- Add support for custom ordering in plugin tables (configurable by overriding the tableOrdering function in the
  table JS class)
- Add support for using device credentials in the Rest Call Service (impact on migration files:
  "username" / "password" => "custom_username" / "custom_password"). Don't allow using device credentials
  if the run method is set to "Run Once".
- Make webssh command configurable from settings / ssh section
- Add new label size property to configure label size in workflow and network builder
- Add new "Configuration" RBAC mode
- Make "sessions" an admin model (visible only to admin users)
- Update git service to support git clone, shallow clone and custom path to local folder (instead of hardcoded path to
  "network_data" folder)
- Update slack notification service to use newest slack_sdk library (instead of slackclient<2)
- Make scrapli connection arguments configurable from automation.json / scrapli / connection_args

Migration:

  - Update all access with new GET / POST endpoints
  - Doc link in settings.json to be updated with custom doc links.
  - Refresh rates in settings.json to be udpated (e.g 10s instead of 3 if RBAC is used)
  - Redis config in settings.json
  - In migration files, replace "default_access: admin" with "admin_only: true"
  - Warn user about REST API run service endpoint new default (True)
  - Update service priority to "current priority + 9" (see migration script in files / script)
  - Update credentials of REST Call services (custom_username, custom_password)
  - Add SSH command in settings.json / ssh section

Version 4.1.0
-------------

- Remove Event Model and Syslog server
- Refactor of the run mechanism. When running a service, a single run is created and saved to the
  database.
- Remove "operation" (any / all) property from pool
- Change the way pool objects are computed: via SQL query instead of pure python:
  better performances expected for large pools.
- Add regex support for SQLite
- Add new "Invert" option for table filtering
- Refactoring of the REST API

  - all requests are handled by the same "monitor requests" function
  - remove dependency to flask_restful and flask_httpauth

- Fix submenu bug when the menu is minimized (gentelella bug)
- Replace prerequisite edge with priority mechanism
- Allow making non-shared service shared and vice-versa (if the shared service doesn't have more than one workflow).
- Separate progress for main devices & iteration devices in workflow builder
- Fix bug where subworkflow device counters not displayed in results when device iteration is used
  Bug report mail: "No status for services in subworkflow with device iteration"
- HTTP requests logging: all requests are now logged by eNMS and not by werkzeug like before.
- Add duplicate button in service table
- Refactor the geographical and Logical View to behave like the workflow builder:

  - List of all pools that contain at least one device or link, stored in user browser local storage
  - Remove default pool mechanism. Remove "visualization_default" property in pool model. By design, the default pool becomes the first pool in alphabetical order
  - Add backward / forward control like the workflow builder

- Rename "monitor_requests" function to "process_requests": impact on plugins
- Add global "factory" and "delete" functions in the workflow builder to create and delete new objects
  from a workflow.
- When refreshing a pool, rbac is now ignored so that the pool "refresh" action result does not depend on the
  user triggering it.
- If a workflow is defined to run on a set of devices, and the user lacks access to one or more devices,
  execute for all accessible devices and fail for the inaccessible devices instead of failing the entire workflow.
- app.service_db was renamed to "service_run_count" and it no longer has an inner "runs" key: the gunicorn
  auto safe restart code that uses it must be updated accordingly.
- Store and commit web SSH session content in backend instead of relying on send beacon mechanism and
  onbeforeunload callback so that the saving of a session does not depend on user behavior
- Refactoring of the forms: all forms are now in eNMS.forms.py. Impact on form import:
  eNMS.forms.automation -> eNMS.forms
- Refactoring of the setup file: replace "from eNMS.setup" with "from eNMS.variables"
- Change model_properties in model from list of properties to dict of property with associated type
- Custom properties defined in properties.json: change type from "boolean" to "bool" and "string" to "str"
  for consistency with rest of codebase
- Add "parent_service_name" property to retrieve all results from a workflow, including subworkflow service
  results (see "Re: [E] Re: Retrieving results via REST"). The parent service is the service corresponding
  to the "parent runtime property".
- Add new "Empty" option in table filters and pool definition to filter based on whether the property
  value is empty or not.
- Add table display with property value constraint when clicking on the charts in the dashboard.
- Add scrapli netconf service
- Move LDAP and TACACS+ server init to environment file instead of custom file. Impact on authentication
  ldap / tacacs functions.
- Add Token-based authentication via REST API. New GET endpoint "/rest/token" to generate a token.
- Separate controller (handling HTTP POST requests) from main application (gluing everything together)
- Add new "ip_address" field in settings.json > app section
- Add paging for REST API search endpoint: new integer parameter "start" to request results from "start"
- Add server time at the bottom of the menu (e.g for scheduling tasks / ease of use)
- Add button in service table to export services in bulk (export all displayed services as .tgz)
- Ability to paste device list (comma or space separated) into a multiple instance field (e.g service device and pool targets)
- Re-add current Run counter to 'Service' and 'Workflow' on the dashboard banner + Active tasks
- Ability to download result as json file + new copy result path to clipboard button in result json editor panel
- Ability to download logs as text file
- When importing existing workflows via service import, remove all existing services and edges from the workflow
- Upload service from laptop instead of checking for file on the instance
- Add Parameterized Form mechanism to update run properties and payload.
- Add new "full results" button to results tree
- Fix bug in WB where multiple services stay selected
- Add confirmation prompt in workflow builder before deletion
- Change default postprocessing mode to "Run on success only"
- Add log in case postprocessing is skipped
- Add SSH key support in generic file transfer service
- Always set "look_for_keys" to False in generic file transfer service - no longer an option
- Add validation_section mechanism: set path to section of the result to validate (default: results["result"])
- Add new "connection_name" mechanism to open multiple parallel connections to the same device in the
  same workflow
- Add new "get_credential" global variable in workflow builder. Used to get a password or a passphrase
  for a netmiko validaiton command or rest call service. For obfuscation purposes.
  mail: Obfuscate Credentials passed into Netmiko Command Line
- Fix data extraction service and operation keyword in set_var
- Don't set status of currently running services to "Aborted" when using a flask CLI command
- Add TextFSM support for the netmiko validation service (+ regression workflow)
- Add stop mechanism for services in the Result table
- Add server name parameter in Run table to specify which server a service was run from.
  Server to be configured from env variable SERVER_NAME and SERVER_ADDR.
- Lock editing / run of Workflow to group of owners

Version 4.0.1
-------------

- Don't update pool during migration import
- Add scalability migration files
- Remove "All", "None" and "Unrelated" options in relationship filtering
- Use join instead of subqueries to improve relationship filtering scalability
- Add form endpoints in rbac files when instantiating custom services
- Fix changelog like pool update not logged bug
- Fix workflow tree mechanism from workflow with superworkflow bug

- Change of all GET endpoints to no longer contain backslash:

  - renaming /table/{type} to {type}_table
  - renaming of /form/{form_type} to "{form_type}_form

- Change of rbac.json structure: list becomes dict, each line can have one of three values:

  - "admin" (not part of RBAC, only admin have access, e.g admin panel, migration etc)
  - "all" (not part of RBAC, everyone has access, e.g dashboard, login, logout etc)
  - "access" (access restricted by RBAC, used to populate access form)

- Add RBAC support for nested submenus


Version 4.0.0
-------------

- Extend pool for users and services.
- Add relation mechanism in table for scalability

  - For each table, add link to relation table
  - Replaces the old "Pool Objects" window in the pool table.
  - New mechanism to add instances to a "relation table", both by individual selection and in bulk by copy pasting a list of names.
  - New mechanism to remove selection from a relation table.

- Add "run service on targets mechanism"

  - run service on a single device and in bulk from service page
  - run service on a single device and in bulk from visualization pages

- Add bulk deletion and bulk edit mechanism for tables

  - Bulk edit (edit all instances filtered in tables)
  - Bulk deletion (delete all instances filtered in tables)

- Add "copy to clipboard" mechanism to get comma-separated list of names of all filtered instances.
- Add 3D network view and 3D Logical View.

  - Add right click menu for property, configuration, run service
  - Add default pools mechanism for large networks.
  - Add run service in bulk on all currently displayed devices mechanism

- Move all visualization settings from settings.json > "visualization" to dedicated visualization.json
- Make the error page colors confiurable per theme (move css colors to theme specific CSS file)
- Use the log level of the parameterized run instead of always using the service log level
- Change field syntax for context help to be 'help="path"' instead of using render_kw={"help": ...}
- Don't update the "creator" field when an existing object is edited
- Add new function "get_neighbors" to retrieve neighboring devices or links of a device
- Refactor the migration import mechanism to better handle class relationships
- Web / Desktop connection to a device is now restrictable to make the users provide their own credentials
  => e.g to prevent inventory device credentials from being used to connect to devices
- Configuration git diff: indicate which is V1 and which is V2. Option to display more context lines, including all of it.
- Improve display of Json property in form (make them collapsed by default)
- Update to new version of Vis.Js (potential workflow builder impact)
- Add mechanism to save only failed results (e.g for config collection workflow)
- New database.json to define engine parameters, import / export properties, many to many relationship, etc.
- Fork based on string value instead of just True / False: new discard mode for the skip mechanism. When using discard, devices do not follow any edge after the skipped service.
- Refactor skip property so that it is no longer a property of the service to avoid side effect of skipping shared services.
- Add new option in pool to invert logic for each property.
- New Option "Update pools after running" for workflow like the configuration management workflow.
- Refactor skip mechanism to work with run once mode service.
- Don't reset run status when running a CLI command with CLI plugins
- Refactor log mechanism to send log to client bit by bit, instead of all run logs at each refresh request
- "No validation" in the service panel is now an option of the "validation condition" instead of the
  "validation method". Migration impact.
- The timestamps like "last runtime", "last failure", etc are now per configuration property. The timestamps are
  all stored per device in a json.file called "timestamps.json". These timestamps properties have been added to
  the configuration table.
- Add ability to hard-code logic to mask password hashes when config is displayed in custom controller.
- Add workflow tree in the workflow builder to visualize workflow and subworkflows as a tree with buttons:
  edit / new mechanism: highlight to teleport to any service. Makes it easier to work with large multi-level workflows.
- Replace gotty with pure python implementation. Save session output with webssh. Need to set ENMS_USER and ENMS_PASSWORD
  like with the scheduler to save the session via REST API. For this to work, admin credentials must be defined via
  two new environment variables: ENMS_USER and ENMS_PASSWORD (same as scheduler)
- Fix bug connection not cached when using iteration values with a standalone service
- Fix bug when exporting table to .csv - column shift if comma in property value
- When scheduling a task, the creator of the service run is not properly set to the user who scheduled
  the task instead of the admin user.
- Add a cap for number of threads when running a service with multiprocessing enabled. Maximum number 
  of threads configurable from settings.json > automation > max process.
- Add runtimes select list in service results window, so you can visualize service results in workflow
  builder.
- Include private properties (custom password, ...) when exporting a service, or migration files.
- New color property for workflow edges.
- Export service now exports to user browser besides exporting the tgz to the eNMS instance.
- Remove Create Pool endpoint in the rest API
- Add python snippet mechanism to troubleshooting (ctrl + alt + click on upper left logo)
- Refactor REST service in case status code is not in (200, 300) to fix validation bug
- Refactoring of the rbac system:

  - Use pools extension to user and services to define user access.
  - Add new "default access" property to choose between creator, admin, and public
  - Remove "group" table (a group is a pool of users)
  - Add "groups" property to user and add "creator" property for pools, devices and links.

- New Credentials mechanism:

  - Credentials can be either username / password or SSH key. Both passwords and SSH key are stored in the Vault (no key file stored on the unix server).
  - Credentials also have an "Enable Password" field to go to enable mode after logging in.
  - Credentials have a priority field; credential object with higher priority is used if multiple available credentials.
  - Credentials have two pools: user pool to define which users can use the credentials, and device pools to define which
    devices the credential can be used for.
  - User "groups" property is now a field. This field can be used to define user pools. Services have the same "groups" property.
    When creating a new service, the groups field will be automatically set to the user groups. This allows services to be automatically
    added to the appropriate pool of services, if the pool of services is defined based on that group property.
  - Credentials can be either "Read - Write" (default) or "Read only". In a top-level service, new "credential type" field
    to choose between "Any", "Read-only" and "Read-write" in order to define which credentials should be used when running
    the service.

- The skip values were renamed from "True" / "False" to "Success" / "Failure".

Version 3.22.4
--------------

- Catch exception in log function when fetching log level from database
- Fix object numbers not updated for manually defined pool
- Catch exception in query rest endpoint when no results found to avoid stacktrace in server logs
- Add "fetch" and "fetch_all" function to workflow global space. Set rbac to "edit" and username to current user
  for both these functions.
- Add "encrypt" function to workflow global space to encrypt password and use substitution in custom passwords.
- Return json object in get result REST endpoint when no results found for consistency.
- Reset service status to "Idle" when reloading the app along with the run status.

Version 3.22.3
--------------

- Add regression workflow for file transfer
- Fix RBAC service run and task scheduling REST API bug
- Fix payload extraction workflow __setitem__ bug
- Add regression workflow with lots of service for scalability testing
- Add regression workflow for skipped service in workflow targets SxS run mode
- Fix rest call service local() scope bug
- Fix get var / set var "devices" keyword bug
- Add jump on connect parameters for netmiko backup service
- Fix skipped query with device in service by service with workflow targets mode bug

Version 3.22.2
--------------

- Fix iteration device factory commit bug
- Fix workflow in service by service with workflow targets skipped service bug
- Add missing rbac endpoints in full + read only access
- Fix device creation empty driver due to Scrapli
- Fix workflow iteration mechanism bug
- Fix workflow skip query bug

Version 3.22.1
--------------

- Add user authentication method in user forms
- Fix settings saving mechanism
- Fix gunicorn multiple workers sqlalchemy post fork session conflict bug
- Dont prevent wrong device GPS coordinates from displaying links in network view
- Fix RBAC bugs
- Add new Scrapli service to send commands / configuration to network device

Version 3.22
------------

- Remove database url from settings. Configured via env variable DATABASE_URL
- Remote scheduler
- Remove TACACS+ parameters from settings, use env variable instead: TACACS_ADDR, TACACS_PASSWORD
- Make REST API accept Tacacs and LDAP credentials (in the last version, if you were using TACACS+ or LDAP, you could authenticate
  in the UI but couldn't make calls to the REST API)
- Remove LDAP parameters from settings. The LDAP authentication is in the custom controller, there is a default
  function that works with a standard LDAP installation, but you can customize however you want.
  The LDAP server is now configured with the env variable LDAP_SERVER.
  The settings contain a new section "database" to enable ldap, database or tacacs authentication.
- Add replier option in send mail mechanism
- Rename "app_log" option to "changelog" in log function for services
- Add new entry in workflow RC menu "Workflow Results Table": contains all results for a given runtime,
  allowing for comparison of results same device / different service, same service / different device, etc.
- Refactor logging mechanism. In settings.json, add new logging sections to configure whether the log
  for a given logger should also be logged as changelog or service log by default.
- RBAC
- Fix authentication bug flask_login and add session timeout mechanism
- Make plugins separate from eNMS in their own folder, add bash script to install/update/uninstall them
- Make the CLI interface a plugins
- Remove summary from service state to improve workflow refresh performances
- Add Dark mode and theme mechanism
- Make search endpoint work with result to retrieve device results
- Allow dictionary and json as custom properties. For json properties, use jsoneditor to let the user edit them.
- Add placeholder as a global variable in a workflow (e.g to be used in the superworkflow)
- Add mechanism for creating custom configuration property
- Refactor data backup services with custom configuration properties. Implement "Operational Data" as
  an example custom property.
- Add new Git service. Replace "git_push_configurations" swiss army knife service with instance of git service.
- Add database fetch/commit retry mechanism to handle deadlocks & other SQL operational errors
- Add validation condition for validation section.

Version 3.21.3
--------------

- Add new plugins mechanism
- Fix bug help panel open when clicking a field or label
- Add error message in the logs when a service is run in per device mode but no devices have been selected.
- Add default port of 22 for TCP ping in ping service
- Disable edit panel on double-click for start/end services of a workflow
- Fix invalid request bug when pressing enter after searching the "add services to workflow" panel
- Forbid "Start", "End" and "Placeholder" for service names
- Fix Result in mail notification for run once mode
- Make Netmiko prompt command service a substitution string in the UI
- Fix wrong jump password when using a Vault
- Fix workflow results recursive display no path in results bug
- Improve "Get Result" REST endpoint: returns 404 error if no run found, run status if a run is found but there are
  no results (e.g job still running), and the results if the job is done.
- Remove wtforms email validator in example service following wtforms 2.3 release

Version 3.21.2
--------------

- Fix rest api update endpoint bug
- Add device results to rest api get_result endpoint
- Rename subservice -> placeholder
- Fix rendering of custom boolean properties
- Fix custom properties accordion in service panel
- Fix service cascade deletion bug with service logs and placeholder
- Fix front-end alert deleting services and make it a success alert
- Fix historical config / oper data comparison mechanism
- Fix bug where superworkflow cannot be cleared from list after selection
- Fix bug placeholder service deletion from workflow
- Make superworkflow a workflow property only. Remove superworkflow targets option
- Display only workflows in the superworkflow drop-down list
- Save alert when displaying python error as an alert
- When using a custom logger, only the actual user content is logged
- Update docs rest API
- Improve log function (custom logger behavior / creator)
- Fix superworkflow bug for standalone services
- Dont display private properties in parameterized run results
- Add Ansible playbook service log to security logger
- Update superworkflow initial payload with placeholder service initial payload
- Dont update netmiko and napalm configuration / oper data backup if empty result / no commands

Version 3.21.1
--------------

- Upgrade JS Panel to v4.10
- Fix jspanel position on long pages with a scrollbar
- Fix placeholder double-click bug
- Fix table display bug
- Fix operational data display bug

Version 3.21
------------

- When entering a subworkflow, the selected runtime is now preserved.
- When running a workflow, the runtime is added to the runtime list in workflow builder and selected.
- Workflow Refresh button now updates the list of runtimes in the workflow builder dropdown of runtimes.
- Duplicating a shared service from the workflow builder now creates a NON SHARED deep copy in the current workflow only.
- Created dedicated category for shared services in "Add services to workflow" tree.
- Implemented "Clear all filters" mechanism for all tables
- When displaying workflow services in service table, all search input resetted (otherwise nothing was displayed)
- Add download buttons for configuration and operational data
- Add button in tables to export search result as CSV file.
- When duplicating top-level workflow, display edit panel
- Fix progress display for service in run once mode in workflow builder
- Multiline field for skip / device query
- Add "Maximum number of retries" property to prevent infinite loop (hardcoded before)
- Add "All" option in relationship filtering (filter object with relation to All)
- Rename "never_update" with "manually_defined"
- Set focus on name field when creating a new instance
- New property in service panel (targets section): Update pools before running.
- Extend the custom properties to all classes including services (displayed in an accordion in first tab).
- Add new search mechanism in the "Add services to workflow" panel
- Add new "Trigger" property for runs to know if they were started from the UI or REST API
- Add time-stamp of when the configuration / oper data displayed was collected
- Ability to display config older config from GIT
- Ability to compare currently displayed config/data to any point in time in the past.
- Syntax highlight option: ability to highlight certain keywords based on regular expression match,
  defined in eNMS/static/lib/codemirror/logsMode. Can be customized.
- New logging property to configure log level for a service or disable logging.
- Fix bug when typing invalid regex for table search (eg "(" )
- Dont display Start / End services in service table
- Make configuration search case-insensitive for inclusion ("Search" REST endpoint + UI)
- Use log level of top-level workflow for all services.
- Add context sensitive help mechanism
- Add keyword so that the "log" function in a service can log to the application log (+ create log object)
- Add timestamp for session logs
- Add device result counter in result tree window
- Move to optional_requirements file and catch import error of all optional libraries:
  ansible, hvac, ldap3, pyats, pynetbox, slackclient>=1.3,<2, tacacs_plus
- Fix Napalm BGP example service
- Fix 404 custom passwords logs from Vault
- Encrypt and decrypt all data going in and out of the vault (b64 / Fernet)
- No longer store user password when external authentication is used (LDAP/TACACS+)
- No longer create / import duplicated edges of the same subtype.
- Add preprocessing code area for all services
- all post processing mode: "run on success" / "run on failure" / "run all the time" selector
- Support functions and classes with set_var / get_var 
- Fix front end bug when displaying the results if they contain a python SET (invalid JSON):
  all non-JSON compliant types are now automatically converted to a string when saving the results in the
  database, and a warning is issue in the service logs.
- Add superworkflow mechanism
- Add jump on connect support
- Add log deletion support from CLI interface
- Forbid import of "os", "subprocess" and "sys" in a python code area in service panel
  (snippet, pre/postprocessing, etc)
- Refactor logging configuration: all the logging are now configured from a file in setup: logging.json
  Besides, the log function in a workflow takes a new parameter "logger" where you can specify a logger name.
  This means you can first add your own loggers in logging.json, then log to them from a workflow.
- Remove CLI fetch, update and delete endpoint (curl to be used instead if you need it from the VM)
- Improve workflow stop mechanism: now hitting stop will try to stop ASAP, not just after the on-going
  service but also after the on-going device, or after the on-going retry (e.g many retries...).
  Besides stop should now work from subworkflow too.

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
- Remove "Enter subworkflow" button in toolbar and add the same button in right-click menu
- Add button to switch to parent workflow

Version 3.18
------------

- Add Operational Data mechanism
- Removed Clustered and 3D View
- Changed configuration to be a .json file instead of env variables
- Removed Custom config and PATH_CUSTOM_CONFIG
- Remove Configuration comparison mechanism
- Display the results of a workflow as a tree
- Change the mechanism to add a service to a workflow to be a tree
- Add the forward and backward control to the service management table.
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
- Removed Clustered and 3D View
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
- Payload extraction refactoring

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
