# Release Notes

Version 5.3: JSON Migration, High Performance Mode and other Performance Improvements
-------------------------------------------------------------------------------------

- Add new JSON migration mechanism
  - Add new "Generic Device" class and convert all devices of type "device" to this new
    "generic_device" type (impact on migration files)
  - Add new "Generic Link" class and convert all devices of type "link" to this new
    "generic_link" type (impact on migration files)
  - Add new "Generic File" class and convert all devices of type "file" to this new
    "generic_file" type (impact on migration files)
  - Add ondelete="SET NULL" constraint for the following foreign keys:
    - Changelog.model_id for all models
    - Data.store_id
    - ConnectionService.named_credential_id
    - LinK.source_id and Link.destination_id
    - RestCallService.named_credential_id
    - WorkflowEdge.workflow_id
    - Commit: 801da3b267df05a3474547330a356577526b8b78
  - Add cascade delete between file and folder to fix json migration import for mysql
    Commit: bc9fe7e3b7bc6938f9ecbc20fb2254d3a4ee6898
  - Refactor runs and results to store state with persistent ID instead of ID to be able to
    persist the state when exporting runs and results as JSON
    Commit: c81c3aceb345134a20c33a389de3eda2fac0cb15 (update state to use persistent ID)
    Commit: e6cac0d8439442ba858d764b135057b8e8b63f9a (move edges to top-level state)
  - Replace legacy bulk_update_mappings and bulk_insert_mappings with new SQLAlchemy syntax
    Commit: 76e9d55829b31ed39ca96cbc62bfb6fb9f54ee29
  - Add batch mechanism for creating and updating DB records in batches during the migration import
    Configured via database.json > "transactions" > "batch_size" (default: 1000)
    Commit: 80e11132115e76c4eab2aa0a5cd0f8361d3c0adc
  - Separate JSON and YAML migration forms
    Commit: 783ad217d188766e767c80b9c5e3b19b7acc4145
  - Update 'migrate' REST endpoint to support new 'import_type' argument (yaml or json) to select the
    corresponding function for import export
    Commit: 1ccfaaf4123276c9ba4c3c9a4d3935c8f5dcb897
- Make Service.name a SmallString, otherwise mysql fails to initialize with the following error:
  "MySQLdb.OperationalError: (1170, BLOB/TEXT column 'name' used in key specification without a key length)"
  Commit: 82154c0830f1cae60ea7a81732478c302767145b
- Increase size of 'payload' field in Rest Call Service
  Commit: c586d0b852a60576c9d0cec5ec134bfc91c04035
- Performance Optimization
  - Update "counters" function to improve dashboard display time
    - Use low-level SQL query to compute Count dictionaries for each model property
      Commit: a01d175e5f4c66c29d250de67fe24cc0b530ec38
    - Get task ID instead of SQLAlchemy objects to get total number of active tasks
      Commit: 975aeadaba5f75af26f62a6b7e1c232a1ccbdae2
  - Update pool mechanism optimization:
    - Replace "db.session.execute(table.insert().values(values))" with
      "db.session.execute(table.insert(), values)" (the update can fail with first option)
      Commit: 94d3ee1828d8ec4b51cd97eb154ed9b15528d4c0
  - Update "get_workflow_services" function (used to copy existing services into a workflow)
    - Use orjson.dumps instead of flask.jsonify to increase function call response time when
      transfering a lot of data to the front-end (e.g 'get_workflow_services' endpoint)
      Commit: 8442ac89436a2802698f12e47b559ef57ce4dda0
    - Query properties ("id", "name", "scoped_name") instead of bulk objects to speed up database
      query execution time
      Commit: 299a85c52ad6749155b1acab215d30f9ec4241da
    - Remove lazy join of Workflow.services and Workflow.edges to speed up db.fetch("workflow") query
      Commit: 0932e2eb7281a6b3755d9a21c7f124b4555c1287
    - Refactor the search to no longer use jstree search mechanism (one ajax call per workflow match), and
      remove the associated "search_workflow_services" function
      Commit: e5b70fb411cfe1d8f1dd42df324a275eb2404946 + 9c62edd8a58cb9dc3a748044a31b0eaa8c26c3d6
  - Optimize call to "filtering/run" when loading the results table, or the device results table
    by removing the lazy joining of Devices in the Result class (Result.device)
    Commit: 9a543b326d83ec3be08e5f98d9be8ee10680d00b
  - Optimize call to "run_service" (slow response when many runs (>1k) because of 'to_dict()' call
    without argument)
    Commit: ecc22a0fecd18c559db9d2414e6c968dca6efd93
  - Update 'save_positions' function to no longer make one SQL query per service / device when saving positions
    Commit: 49eb0e18862efaacf61f415ac45295038283b1cc
  - Bug Fix: Optimize the workflow builder refresh mechanism to update service color in bulk via nodeUpdates
    When refreshing a large workflow with a set runtime (i.e not in Normal Display), the update would
    cause the UI to freeze for a few seconds. Should be instantaneous now.
    Commit: 5476991c10f91b0e8a3836d3ace7cbbc102616ea
  - Optimize 'add_instances_in_bulk' to use name_in SQL query to add instances by name instead of db.fetch
    in a loop and return the list of all objects whose name is not found, not just the first one
    Commit: c44abaa30936d347afd3bbd64188153c0006787d
  - Update skip_services endpoint to not fetch services in a loop
    Commit: a03720c560496e98a3fa061a5ea5088436c20431
  - Update "get_service_state" function:
    - Optimize the function when a workflow has many runs by only fetching the runs name and runtime
      properties, not the full SQLalchemy objects for all runs (fetch the SQL object only for
      currently displayed runtime instead)
      Commit: 7fe70bc8cf5f453bb45d75878fa070e9800f9edb
  - File Optimizations:
    - Add missing index on File.folder_path column (used for file table hierarchical filtering) to make the display faster
      Commit: 949c5ab9f398027acdd8c5c7e93a2b1b3de7f206
    - Speed up the "Scan Folder" mechanism:
      - Remove the SQL relationship between File and Folder (rely on folder_path only to display the table)
      - Refactor the "scan_folder" function to use os.scandir to gather file data, then create new files
        and flders in bulk with a low-level SQL query
      Commit: 52c6ad85f61392177044b98bb3f5be1555736220
  - Optimize the workflow duplication mechanism:
    - Don't return anything in the post_update function, and update the 'controller.update' function to not
      rely on the post_update function to return the instance properties and relations
      Commit:
        - e590b0b512a9e904dc3dc6d2a52632d78815ba48
        - c48059f8182e0fa0bf915c11c1ea822b31415006
    - Only call the 'recursive_update' function from the top-level workflow
      Commit: e83dcc7739f12406ea802295afab684d2d7ad001
    - Avoid creating changelogs during the workflow duplication mechanism
      Commit: 370b580602ed47bde69f3bbe83deccb541876215
    - Allow passing SQLAlchemy object in Base.update (via factory) to reduce the number of fetch queries
      Commit: 217ad4517477fab06f26b91d845fffb51ea20178
    - Don't create changelog objects in SQL creation and deletion de detection events if connection info set to ignore
      Commit: a58b79edbbd621548abb27112f1f0686d548e431
  - Remove calls to "to_dict()" with empty parameters (gets all relationships - not scalable)
    - Update to the Excel topology import mechanism:
      - Don't call to_dict() after creating an object
      - Don't update pools after the topology import
      Commit: 52243ef833579e31ff631d9b70b739aa5ce201ac
    - Use 'get_properties' instead of 'to_dict()' in the add_objects_to_network function
      Commit: 2747699d47a6443e712ce2f4490c06536c7daed7
    - Use 'get_properties' instead of 'to_dict()' in copy_service_in_workflow function
      Commit: 00603dac5d6131c6c3289de764ee98d4db4af866
    - Call 'get_properties' instead of 'to_dict()' in db.delete_instance (and therefore db.delete)
      Commit: 84acd8d02c69bdb8bc75daf44771cec72a202c2c
  - Other SQL optimizations:
    - Remove Run.service lazy join (workflows run slightly faster)
      Commit: c1525d9295bf70d14b192d6cb942cf299a60c9f9
    - Reduce numnber of unnecessary calls to db.fetch in Runner initialization
      Commit: c7847256a06b7c12207a6db7b8f60719ff8f2403
  - Changelog Display:
    - Add python snippet to create many fake changelogs with low-level SQL (50M by default)
      Commit: a302b25ed825dc967c4db61a29f32367ee4ccf33
    - Add an index for all changelog models
      Commit: 25a719efe5659e633710917f0e9ccf9744ddc6e7
      Impact: creating 50M is about 5x slower, but changelog table performance issue is fixed
    - Update SQL constraints when opening service changelog panel from RC menu in the Workflow Builder
      to make it faster
      Commit: b7eae51e4fe7a3076a7c94ea9a78ee2a659de0ee
- Minor update to configureNamespace function
  Commit: 891c255945ab85cf8e7c970805c4498a0adfa081
- Refactor the SQL query monitoring mechanism:
  - Compute the query duration without executing it twice
    Commit: 65fe27e2f97cb79828ef5d35a4d69f01dda6c2ea
  - Add traceback to find out which line of code sent the query
    Commit: 4becbb44f6194be2ecdd9e68eb1a94f074d98f4e
  - Display number of queries in the UI for easier monitoring (after eNMS version)
    Commit: bc6a5840070bac30262c4f8392179e44ef096c4d
- Remove lazy join for workflow edges and servers
    - WorkflowEdge.source, WorkflowEdge.destination, WorkflowEdge.workflow
    - Server.workers
  Commit: df2b92f8de2a1b23b1387f4596c07379a8c6e450
- Run Targets Devices and Pools association and Run Allowed Targets Update:
  - Rename "vs.run_targets" to "vs.run_allowed_targets": Commit 267a3fe7abd2bf196139d2cc8828e864acc7ce46
  - Move the restricted target computation outside of the compute_devices query so it works for
    workflow targets and iteration targets too
    Commit: 29c07275f935dae159eff80fff298e5dcdcde31d + 9bb96827e7f5bd09c79834b68b31cc3943165a24
- Remove update all pools after running option (unused, not scalable)
  Commit: 0e0192e48819890de590d83f494ef9a05d5b8e17
- Set netmiko log level to 'info' in logging.json > 'external_loggers'
  Commit: 0fd78af2824b8e2c6904085f27387a53824d44d1
- Set scrapli and paramiko.transport log level to 'info' in logging.json > 'external_loggers'
  Commit: 0bb00e8de45da0cb88777f0fc5df3bc2323b0986
- Increase maximum number of threads to 1000
- Make the orjson library mandatory (move from requirements_optional.txt to requirement.txt)
  Commit: 9f30e17d5c5a2d52b7a63bcb2b7b0a3068a36fce
- Refactor netmiko and scrapli backup services to move the 'last_property_runtime update in the SQL transaction
  Commit: 2f3071e4bddf26a9c7ffbc56950d819b0328f96f
- Refactoring of objectify:
  - Add support for properties in fetch function
  - Use 'in_' query to convert names to ID in form_postprocessing function
    Commit: 14664e221fc19829ef6f0e39ed3c41d9becea241
  - Update fetch to support 'in_' queries (syntax: "property_in=[p1, p2, ...]")
  - Update objectify to use 'in_' query via fetch_all instead of fetch in a loop
  - Don't call objectify in Base.update if value is empty
    Commit: 53a24913d886c0e6ce96aa747802b6c51b30604f
  - In form MultipleInstanceField validation, use in_ query instead of fetching objects in a loop
    Commit: 956f796b6e282fe31d446d5022f17858b646d719
    Performance speedup: edit object ("Save" button in Edit Panel) about 10x faster for a workflow
    with 1k target devices
  - Remove all references to objectify and replace them with 'fetch_all' with 'in_' query
    Commit: c6a070a45816b1146cb9fc3ec3b5930e404c685f
  - Refactor the update_instance REST endpoint: move controller.objectify in update_instance function and use
    db.fetch_all with 'in_' query instead of fetch in a loop
    Commit: fbfdf587b0ed5a2c99246cc85ee87ed517b696de
- Move the 'runtime' property to the first column of the Run ('Results') table so that runs are always
  sorted by runtime, even when they have custom names via parameterized form.
  Commit: b7839556dc70844af5efe3c851e2b69ee41ec0eb
- Change memory_size from an Integer to a String in database (to avoid integer overflow issue)
  Commit: 9d4ff3f4e78a2db97c7c2937160a65f91f07737c
- Rename function in runner.py
  - get_results: run_job_and_collect_results
  - compute_devices: compute_run_targets
  - get_device_result: get_device_result_in_process
  - device_run: compute_targets_and_collect_results
- Add new "scan_folder_on_startup" option to make calling "scan_folder" on first app init optional
  Commit: 0378806a6d42aa1ab6fc349e37dd3389bcf8f722
- Remove 'get_device_logs' endpoint in rbac.json and in controller code (unused, no longer relevant)
  Commit: 636cf96ed26dd3ff9fdd411fad27b61e4fc11633
- Remove 'clear_results' endpoint in rbac.json and in controller code (unused, no longer relevant)
  Commit: 7e65a387d4b2dffa0423fcffe67a750d6da6717e
- Update bulk edit mechanism to take the bulk filtering form into account when filtering (previously,
  bulk edit does not work with relationship filtering, e.g find all services that belong to a workflow
  then bulk edit filtered services)
  Commit: ca721c4b4ce9036cd006e72e04e12ddc4096ea17
- Fix display bug in the Network / Workflow builder when moving a node, then switching to the edge creation
  mode, then dragging the background of the canvas: the first node is moved instead of the canvas because
  of a vis.js bug that does not properly clear the internal state of the canvas dragging mechanism
  Commit: a48091f61033c5e4cd0c98b842e62a5561a1fcc9
- Make 'get_git_content' and 'scan_folder' optional on app startup with new optional "on_startup" key
  in settings.json
  Commit: 4341a0feebed970625e677a85c52a7a0f29d6d7a
- Allow raising custom 403 alerts in the UI from a plugin or any controller function, instead of the standard
  'Not Authorized' message
  Commit: 67cd0ce9e51a1202d9132c3f1d2993bbfced4ba8
- Changelog Diff Improvements:
  - Make 'Side by Side' the default visualization mode and increase panel width
    Commit: c5e0af196abe701e8480e4109edb26c2f7603797
  - Remove the newline in the content of a changelog before 'Added' and 'Removed' so it can be searched in the changelog
    table, and add the diff in Changelog.history so that updates to an object relationships can be displayed in the git
    diff panel of a changelog
    Commit: ccf6d7a4de6490689e5a094c351e273ccfe150fb
- Refactoring of "Last Modified" properties:
  - Add 'Last Modified' and 'Last Modified By' properties to the User, Group and Server classes
    Commit: 2e8f4196411ade6b37e0c63039af1c0d9879f8ea
  - Add 'Last Modified' and 'Last Modified By' properties to the Credential and Pool classes and move last modified update in Base.update
    Commit: 88254128498d50d015070d9eacdf8819c0669999
  - Add 'Last Modified' and 'Last Modified By' to service and task forms, as well as group, task, user and server tables
    Commit: 26c547bc025a682c1aad887b3d044adf49fc9b7b
- Fix edge display (workflow edge in workflow builder and link in network builder) not updated after either name or
  color is modified bug
  Commit: 45596d6a40314d57c6aaf6538c4bc6bc61b04877
- Fix bug in workflow builder: if user selects node A (single left click), then drags node B (without selecting it),
  then drag node A again, node B is being dragged instead of node A. to fix it, when dragStart is emitted, we check
  whether the node being dragged is selected or not; if it is not, we select it
  Commit: 45de53534d0095bf719e5652febdf7d782db0edd
- Refactor REST Call Service to store payload as string instead of JSON
  - Convert payload field to StringField instead of DictField
  - Add a new property "Substitution Type":
    - String Substitution: the payload is not a valid dict in itself: it will be substituted first, then converted from a
      string to an actual dictionary with ast.literal_eval before using it as "json" argument
    - Dict Substitution: the payload is a valid dictionary represented as a string: it is first converted to an actual
      dictionary with json.loads, then it is substituted (ensures backward-compatiblity)
    By default, the property is set to String Substitution, but migrated services are using the Dict Substitution option.
  Key commit: 0dd36637610853ebd6a47058602736d11740a55f
  - If the 'Subtitution Type' is set to 'Dict Substitution', validate the payload field by converting it to a JSON object
    with json.loads (replaces the "json_only" option of DictField previously)
    Commiy: 49874c2282fd443fa6be65321c84309e483bbc74
  - NOTE: check whether Dict Substitution is truly needed, or if legacy REST services can be
    made to use string substitution instead; if it works, dict substitution can be removed.
- Outgoing Edge Mechanism:
  - Refactor the graph traversal algorithm to allow for edges other than success and failure: the user can define
    an "outgoing_edge" variable in python (e.g in post-processing) to decide which edge to follow next
    Commit: b8c37c1bdb0e2b1c0775b475366de7965a2e8f7a
  - Update the Workflow Builder to support displaying multiple edges between two services
    Commit: 8efa2d41165b285083544695d5a6bbb44908fbda
  - Add new regression workflow: "Outgoing Edge Mechanism"
- Add 'Export as CSV' buttons in Runs table (Results page) and Tasks table (Scheduling page)
  Commit: 007c96d5a9635f60faa99e15cfbb1d8169dcf529
- Add 'Copy Search to Clipboard' feature:
  - Add new button in the top-level menu of a table to copy a link to a table with the current search
    parameters (either per-column search from the table, or bulk filter including relationships search
    from the bulk filter form)
    Commit: 62a790a3b1363ff705ace6a1a382dcfa0c25492a
  - Don't include columns data (which columns are visiblles and not visibles) in hyperlink to keep hyperlink
    length small (nginx issue with long links)
    Commit: b32b9a6a7b2325df134324a70ae39a241efd3ce9
- Configure the folder name for configuration backup in automation.json 'configuration_backup' / 'folder' instead of
  hardcoding it
  Commit: 17ebe08db3a63a55483a81ed6f83f9457baf0200
- Add 'creation_time' property to Server class, form and table
  Commit: 672c80df874465cd26dbace8e247573bff3935f0
- Fix bug where service targets are not copied when duplicating a workflow (e.g a workflow in SxS service targets mode)
  Commit: 4f4cbf22d937e228412cda61133b6731c9ccdc2f
- Remove charset utf-8 from redis configuration in settings.json (no longer supported)
  Commit: 85fb006a5d3a476f88693f8228b2115c9f1d051c
- When refreshing logs with a redis queue, don't always fetch all logs from redis, only fetch the logs up to start_line
  as provided by the front-end (fixes the wrong implementation in a6660f78805d9475d68441c0b042d67ce03925e6 and the
  associated issue 541)
  Commit: 0a382bf07126fd8a5b3af420e692278761adb636
- Add new "size" property to Files to see filesize on disk in form and table
  Commit: 0e0bd259d6267cc1c2a7f0bd618fb14067a985b9
- Normalize strings in the front-end during form serialization to remove windows and mac line endings so that changelogs
  don't get created for line ending changes
  Commit: 480e044ed214102154bac1f6b8db5bb8f7a531bf
- Add new Rate Limiter Feature:
  - Limit the number of on-going runs in parallel allowed for each user (configured from
    settings.json / "rate_limiter" / "runs")
    Commit: 2db5c5d74c9962a11c202009c8122dcf37c74667
  - Limit the number of HTTP requests a user can make with configurable fixed windows:
    - Configured from settings.json / "rate_limiter" / "requests"
    - A window is defined with the following parameters:
      - "window_size": duration of the window (in seconds)
      - "max_requests": maximum number of requests allowed during the window
      - "rest_api" (bool): the window applies to REST requests only
- Improve the JS table search code to prevent sending multiple searches in parallel to the server:
  - Always wait until the on-going search completes
    Commit: 0a6bbb43555913b5fdd50351d0ee16e456fa4e93
  - Add refresh settings in settings.json to configure search behavior
    - "timer": debounce timer (search start X ms after last keystroke)
    - "notification": send notification in the UI to let the user know that the start started / completed
    Commit: 0f8e011f71a13e03cff8382aa0b972a6c7b147db
- Don't create changelog for the 'last_{property}_{timestamp}' properties in Device class to prevent logging
  too many changes
  Commit: 395a34dcdb13a10d61fc8131b26eea04828e34f3
- Refactor Device.serialized and Service.serialized to no longer store the serialized string in the database
  to avoid data duplication:
  - Instead use get_properties() in the workflow builder search, and a combination
  of ilike filter on all string properties in the table search
  Commit: 0fa9e72200c2347ec0421513488f1621c04daf55
  - Exclude deferred properties from the serialized search in ilike filter
    Commit: 06fdb14a12bc1969ebfd0e337f597d75980f09aa
- Remove start_service_id from Run class (unused, legacy code)
  Commit: fb75b72be870420fbc9d6388c07f209d5761a6ad
- New Snippet Mechanism:
  - Create a new "Snippet" model for the admin users to run custom python snippets for app troubleshooting
    and maintenance
  - Convert all the python snippets that were previously stored in the "snippets" folder to Snippet object
    (stored in the database)
  - Remove the "Per Type Database Deletion" mechanism from the admin panel and replace it with a snippet
    called "Database Mass Deletion"
    Commit: 39081e98a3127fb825bcf6d44c7a437d6518e89d
- Add one-to-many Server - Session relationship to identify which Server handled which Session, and
  update the Session (resp. Server) table with a 'Server Name' (resp. 'Sessions') column
  Commit: 2650f509a77107e7795915ecb408b9f75814b2c9
- Add new 'delete_if_not_found' option for files so that a file is deleted during the scan folder mechanism
  if it is not found on disk (configured from settings.json / "files" / "delete_if_not_found" (default: true))
  Commit: 4290d0e38b3c53563e96952f9503d116ecc8e9f1
- Remove device connection dict from 'connection_cache' in disconnect function if there are no other connections
  for that given, otherwise the connection count in 'check_connection_numbers' is wrong
  Commit: e60f90986732aae7e1943662f1553a05fe75b5c2
- Fix JS error in console when skipping or unskipping services because of slash in tooltip: replace slash with dash
  Commit: 0d6cf0fb599f72064f1a46a3bff113ceb8d35945
- Add new 'polling_interval' setting to configure the polling interval of the file monitoring mechanism with
  watchdog PollingObserver
  Commit: 259549c2355cd113e82a7e083baf31165c428ba0
- Decouple the File Monitoring process with watchdog from the main app:
  - The File Monitoring process must be started independently from the main app, with the FILE_WATCHER
    environment variable set to 1
  - Remove the "monitor_filesystem" variable from settings.json
  Commit: 080f5ca9b3dcae041a73736199403e7f6ef8222b
- Don't trigger UI refresh if the tab does not have focus (for table refresh, network builder refresh and
  workflow builder refresh)
  Commit: 75939e4c8f98895b3f4a77e8b025a4f38db67391
- Add new 'result_dict' variable in the results that contain the 'results' before post processing (useful to get 
  device output in services like netmiko commands in case post-processing is failing because the 'result' variable
  then becomes the stacktrace) (reported in support slack channel)
  Commit: 890cf5cc213b87a944d75333ee695820ffcb6f2e
- Update 'db.fetch_all': rename the first argument from 'model' to 'instance_type' so that it can be used to fetch
  all devices based on their 'model' property (no more conflict between 'model' first argument and 'model' coming
  from **kwargs)
  Commit: 301fdba13afe9f6c526582c03f1a8b221d4eb2a6
- Update netmiko command service to always return the result as a list if 'Results as List' option is checked,
  even if there is a single command
  Commit: fe812c22b2325f2cbec16d100eb508ed2087780d
- Make Device.ip_address an indexed column
  Commit: 2ea2722573f58440a18447d79a7250db87cc0cc4
- Fix bug #568 where a service that fails at compute target device query step is marked as success in the workflow
  builder (update how 'runtime' and 'success' are stored in the state)
  Commit: 3fe31e330ab3cb8b28d4a8c146bf26f7ee2d5f81
- Fix bug #569: when there are already device objects in a query field, return them immediately
  Commit: 30c458c5f7f6285bd8a9b91ed2f068b988718f49
- Fix bug where 'last_scheduled_by' remains empty when its not set and the task is scheduled by an admin user
  Commit: a448f00f4730f9c4a625bcd5294e6db39a028527
- Fix blank space in bootstrap selectpicker list in the workflow or network builder when there are many entries
  Commit: 05a2810722ac4d585f4902c94725e8d53c630cb3
- Fix return carriage bug in 'Device - Iteration' progress label of a service in the workflow builder
  Commit: f6893cb6f8c150c696236b8ae5e308d57742f3fe
- Fix bug wrong device result display with specific color: empty vis.js node coming from the top-level workflow bug
  Commit: 8076b25f2df876d4fde81f4d42c31c676be0f281
- Add new "allow_redirects" option in REST Call Service
  Commit: 8dd630c906f44635e503b416cd03cab826c3f89d
- Refactor "Stop Run" mechanism:
  - Require "run" RBAC access for a user to be allowed to stop a workflow
  - Add new "You don't have permission to stop this workflow." alert in the UI
  Commit: 40589d9e2dffa2b2672ce8415bb8ba20facdc019
- Update the REST Call Service with new "proxies" option
  Commit: 6da2c403abe466522968ba0ea38393f8e4d74e08
- Make "Scan Folder" mechanism available to admin users via REST ("scan_folder" POST endpoint)
  Commit: 74d9894b807a7984fb667f644517a74af9f7933a
- Fix bug label and color of the edges not preserved when duplicating a workflow
  Commit: 075bf450767ee1cdba3aa7919415dd6e9ffa2d12
- Fix bug freeze after duplicating task with admin user when the task was created by a
  non-admin user because of RBAC relationships (email "Scheduling issue - causing lockup")
  Commit: 9b9684adf160607fc002f8983871e8b8bd6635e
- Add session scope when trying to create worker to avoid race conditions when running many
  concurrent calls in parallel
  Commit: ec6e4b3f8dfb312128714436088dadfa24e4c62f

Key Ideas about the refactoring of runner.py and "High Performance":
- Committing changes one by one takes more time (in particular, every result is created and committed in its
  own transaction)
- Every commit during a run makes the SQLAlchemy session expires, along with all objects attached to that session:
  - The next time an object is used (e.g "device.id", "device.name"), a SQL query is sent to the database
    under the hood to refetch the object. The number of refetch during a run becomes
    "number of commit" * "number of objects used"
  - If multithreading is used, the commit of a shared session will result in "Out of Session" errors and cause
    the workflow to fail
  - For a single run with ~ 1000 device targets, we can get up to 1M SQL query to the database
- Users should not have access to SQLAlchemy objects (e.g device via the substitution mechanism or any of the
  python field), because they can then modify them in a way that we cannot control ("device.property = ...")
- Separate the code that pertains to the main run (executed only for the top-level instance of Runner, therefore
  it makes more sense for it to belong to the Run class) from the code that is executed for every instance of Runner.
- The threaded SQL ("refetch after fork") causes two major issues:
  - It limits the number of threads that can be spawned (must be less than currently available pool connections).
  - Pool connections are not properly released after a thread ends, so a "QueuePool limit reached" exception is
    raised after multithreading has exhausted all connections. The number of available connections in the SQL
    connection pool should not determine the number of threads that can be used in multiprocessing mode.
  - Objects attached to a session expire on commit (default SQLAlchemy setting),but they don't expire on remove,
    so fetching an object, calling db.session.remove() and accessing object properties should not trigger a refetch.
    In refetch after fork with "High Performance" enabled, we refetch the devices, then remove the session; everything else
    is a namespace
- In "No SQL mode", every transaction that happens after forking should have a clear beginning and end, otherwise the
  session is never closed until the end of the thread, and a workflow that uses 25 threads will use 25 SQL session
  until the end of the wokrflow.

Main Commits of the Run Refactoring:
- Part 1: Generate the workflow topology graph at the beginning and reuse in
  workflow job function to reduce the number of SQL queries, and remove the neighbors SQL
  query to get next services in Dijkstra.
  Commit:
    - 6adb7b7cded5484a83de497757edcd2bf6313e55
    - bf4293d49690429ec1b4c74f6289d652fddf89f4
    - f8182fcda6c2a97db0429173a2d35942834373f5
    - d55771ef9a515f76ab04df6f248ab78733c6a23c
  Side-effect: Because the workflow topology is saved when the workflow runs, any changes made
  afterward (such as removing an edge or a service) won't affect that workflow run.
- Part 2 (High Performance Mode only): Store results in a dict and create them in the end of run transaction.
  Only active when the "High Performance" option is checked.
  Commit: 1dce0d1494fe3c3689d27acd68d8e620b49675b0
- Part 3 (High Performance Mode only):
  - Use service namespace instead of service SQL object for Runner.service
  - Convert all jobs to @staticmethod so it can be called without service SQL object
  - Add Target Devices and Target Pools as namespaces to the topology store (SxS with Service Targets)
  - Move the run_service_table update in the end_of_run_cleanup function and use try_commit along with low level SQL to make it faster
  - In the workflow, fetch the service with db.fetch or use the service namespace depending on the value of "High Performance"
  Commit: c4110615e6c36832d183ad0edf37a595cbc39ea6
- Part 4:
  - All Services are Namespaces
  - All Devices are SQLAlchemy objects
  Commit: 71bf1a7b7a226eb48aa015cc07ed3deff7978b1e
- Part 5:
  - Refactor "Compute Target Pools" mechanism: pools are updated before the main run starts for all services "High Performance"
  - Make commit optional and False by default in compute_pool
  Commit: 1e47b0aef2587055e02f849c45f96a294aff62e9
- Part 6: Use itertools.batched for creating results in batch with bulk insert at the end of a run
  Configured via database.json > "transactions" > "batch_size" (default: 1000)
  Commit: 3fe07068a483175b02a5c16b3bd5663f84d359e6
- Part 7: Remove task from the argument of Runner (no longer used)
  Commit: 99bbad31b0791a71cf61a223c2facfab600572cf
- Part 8 (High Performance Mode only): Create all reports after the main run in the Run class in
  "High Performance" mode
  Commit: 24bd32010b1c94f12680dda13bbf481430fb3e09
- Part 9 (High Performance Mode only): Implement in-memory get transient result function and convert devices to
  namespace in topology cache
  Commit: 1b403f8b2f93e0ab37baea5738b36ad9493612f1
- Part 10: Move the initialization of the main run cache in the Run class
  Commit: eb66e66689e8e39ab523575e79badb379b3ed370
- Part 11 (High Performance Mode only): Update Runner.log and env.log to not create a changelog object with factory
  during a run if the run is in no SQL mode (logs are stored in memory in vs.service_changelog)
  Commit: c2bb5b7698c63a938a020bd7b6f6302486f2035d
- Part 12: Move 'close_remaining_connections' function in the Run class (it is executed after the
  main run has done running)
  Commit: 3ba8f7ee6c5c7cb874e80c7d28b6f253605ebc46
- Part 13: Close the threaded session used to refetch after fork immediately after refetching to
  avoid blocking the session until the end of the thread
  Commit: 8d62843fb91525a7a4569b42d2e5382029859d4f
- Part 14 (High Performance Mode only): In no SQL mode, pass a namespace of the Run object instead of the Run itself,
  and remove the placeholder argument
  Commit: 6fce929592b61e6314b437b4de4566ea33d9ea3e
- Part 15 (High Performance Mode only): Don't refetch after fork in "High Performance" mode
  Commit: f4b1f8e7f1b78bbcb81b35c81b31d34fb2af9be0
- Part 16:
  - (High Performance Mode only) Don't pass reference to restart_run as Runner arg in no SQL mode
  - Remove references to restart_run in Workflow.job
  - (High Performance Mode only) Compute targets at the end of run in no SQL mode
  Commit: 54e548559fa8722580c934858547a852b237ccda
- Part 17: Call db.session.remove at the end of Controller.run to release the SQLAlchemy connection
  to the connection pool
  Commit: 265dee6193b907a7f85f361916379a6eede5a826
- Part 18 (no SQL only, major issue): Add db.session.remove() after calling db.get_credential to close the SQLAconnection
  after fetching the credential object in a thread, and prevent leaking SQLAlchemy connections when the connection
  setup fails (only applicable if multiprocessing is enabled)
  Commit: 0522ca6131d6679f827b6a8ff18b536960ec1766
- Part 19 (High Performance Mode only): Fetch device with selectinload gateways to prevent refetch in connection functions 
  Commit: e04d7a334c135cd9a73e65c49c6421e4429481e5
- Part 20 (High Performance Mode only): Refactor the "compute devices" mechanism and "get_target_property" so that targets are
  computed in the Run class whenever possible (e.g parameterized form, restart run, etc)
  Commit: 5929b7ed82aa0c4f56c08a64182c6040319e8e5b
- Part 21: Move all the global variables function in their own class, parent class of Runner
  Commit: 80684829483cdb8157993087d80b2ab960195201
- Part 22: Move the 'space_deleter' function to the Variable Store
  Commit: 0f124252bb253de4d826162fd3610233db745741
- Part 23: Move Runner._initialize in the Run class and refactor the aborted run logs and results creation process
  Commit: dec10325858094969cefb6e1931987729ac04aac
- Part 24: Fix run_services association and subsequent creation of subservice logs in case a run is interrupted by app reload
  Commit: b851cd930490cf589520edc70135256af8f4399d
- Part 25: Store transient results in the redis queue if there is one, and recreate all results from the redis queue
  (even if the run is interrupted by application reload)
  Commit: a153abc049f28e998bf7a40648c85c5ce23bea46
- Part 26: Remove 'trigger' property from the results
  Commit: f0396da7ad4a64bc53dfb0bf955c4c355773e30f
- Part 27: return results in 'start_run' instead of storing them in 'self.results' and add the device
  results to the main results in the Run class (in case the trigger is REST API and mode is no SQL)
  Commit: b559794d79e9d3599631f2b8a409a90d78911f30
- Part 28: in 'High Performance' mode, increase the maximum number of threads allowed to 'max_process' * 10
  Commit: f26ee4f41310de0d488f548afb8476efe6674f0c
- Part 29: (High Performance Mode only) Refactor 'compute_devices_from_query':
  - Use a 'in_' query to fetch the devices, which reduces the number of SQL queries made during the run
    Commit: 4840ab57130c7a189be846da83cb210991fdf622
  - Add db.session_scope context manager to release the SQL session when multiprocessing is enabled
    Commit: 27f4652e12427dfb9409e7e7bc71cd06e8240e8b
- Part 30: Refactor netmiko and scrapli backup services to handle all SQL operations in a single function, and remove the
  session at the end if in high performance and in a thread
  Commit: 5cb6f847650dfb00173e69ee674ecf
- Part 31: (High Performance Mode only) In the Ansible Playbook Service, refetch the device object before
  calling 'get_properties', otherwise we get out of session exceptions because get_properties causes SQLAlchemy
  to trigger SQL queries to get some of the device properties
  Commit: 293e09d11ab1eabc831aca40d4d03ae8f5c94f71
- Part 32: Update to the session_scope context manager:
  - Call session.remove() instead of session.close() (because db.session is a scoped_session)
    Commit: 659cbc3302f769e425fd103aff3e3877669d8e38
  - Use session_scope in runner code to remove session after fetch
    Commit: b2e827b832c0470527f0f66ebe188995fe1727fd
  - Update 'get_data' to return data as a namespace instead of a SQL alchemy object, and add session_scope
    context_manager to remove SQLAlchemy session in no SQL mode for 'get_data' and 'get_credential'
    global functions
    Commit: 82f5add1f5e1a465561857a1ab6ea218b1bbb00e
  - Refactor 'get_result' to use db.session_scope to remove the SQL session after fetching the results
    in no SQL mode
    Commit: 90e5405e465da2f9e3b8a12fdeb8ac29e40ce828
  - Update 'get_secret' to use a session_scope to fetch the secret object
    Commit: 9fa66c3842d55ca1c0ff0235ebb399d1f46164f9
  - Add session_scope context_manager in internal_function (factory, fetch, fetch_all and delete) in
    no SQL mode
    Commit: 737bfb4ecb3297c1113d23440341e39e8bd07383

Related Commits:
- Cache the 'global_variables' dict once at the beginning of a run to avoid recomputing it every
  time the 'global_variables' function is called.
  Commit:
    - fd356528ca691e263be0ced18cdf5038a237d752
    - 2f2786f38eb29ba75ac9e2d4eb616c0c7aeef2b4
- Don't compute "target_devices" if it has already been defined as an argument of the Runner class
  Commit: d46230319af9e3a76313584a93e59ac8835efedb
- Replace / rename "target_devices" with "run_targets" in Runner to prevent confusion between
  run.service.target_devices and run.target_devices.
  Commit: 2d7cafc22f08f2d93b383888a6c47c0ec7dfcdb0
- Move all functions related to the main run in the Run class (end of run transaction,
  end of run cleanup, etc)
  Commit: 6b0c37bcfc2f1ee3c99006331c9a3de9e5885b7f
- Remove duplicate progress function in Runner class and use Persistent ID to retrieve device progress
  Commit: 4ac0d4ce9f0f2113e1a5dfd8d3f242f70c520718

Benchmark (comparison last release versus new release) needed for:
- Workflow runs duration
  - Workflow with 5 empty python snippet services, 10k target devices
  - Configuration Backup Workflow:
    - Compare performance new and last release with same number of threads
    - Try to raise the number of threads to 300, 500
- Update pool:
  - Update 1 pool with 50k devices
  - Update all pools (the pools must be the same in last release and new release)
- Workflow Duplication: try to duplicate large workflows
- JSON Import Export Mechanism:
  - Compare speed of YAML versus JSON, for both Import and Export
  - Compare Speed of JSON Import with Structured Data versus Bytestring Data
- Compare Speed to display Changelog panel:
  - In the Changelog page in the menu (display ALL changelogs)
  - In every table in the application (display changelogs related to a specific object):
    need to test every table to make sure no index is missing
  - In the Workflow Builder (resp. Network Builder):
    - For a specific service (resp. device) from the RC menu (Display / Changelogs)
    - For the workflow (resp. network) in the top-level menu: the changelog of a workflow (resp. network)
      should be the union of all services (resp. devices) changelogs, including the changelogs in
      subworkflows (resp. subnetworks)
- Compare Speed to display the Dashboard, specifically the following endpoints:
  - "count_models" (called when loading the dashboard page)
  - "counters" (called when changing entry in one of the property list in the dashboard)
- Compare the "Add Services to Workflow" speed ("get_workflow_services" endpoint), both with and without an active search
- Compare speed to load the Results table (including the 'All Results' panel)
- Compare speed of "run_service" endpoint (time between click on "Run" button and the run actually starting)
- Compare speed of calls to "save_positions" endpoint (e.g triggered when moving a service in the Workflow Builder)
- Compare speed of the "Add Instances in Bulk" mechanism (when adding many objects, for example 10k devices to a pool)
- Compare speed of "get_service_state" endpoint (called every few seconds to refresh Workflow Builder) on large workflows:
  - In both "Normal Display" and "Runtime Display"
  - Both with Workflow Tree open and closed
- Compare Speed for File Mechanism:
  - File Table Display (calls to "filtering/file"): both in "Hierarchical" and "Flat" display
  - Scan Folder mechanism
- Compare Speed of Workflow Duplication (for workflows of different sizes)
- Compare Speed of Service / Workflow Editing ("update/{service_type}" endpoint)
- Compare Speed of Log Refresh when running a workflow (calls to "get_service_logs" endpoint)

Previous Release:
- Workflow with 5 empty python snippet services, 1k target devices
  - DxD: 60s
  - SxS WT: 2s
- Update a pool with 10k devices: 190ms / 50k devices: 850ms
- Add 10k devices to a manually defined pool (Add instances in Bulk): 3.9s
- Calls to "save_positions" endpoint in "Large Workflow": 30ms
- Time of Workflow Duplication for "Large Workflow": 370ms
- Large Workflow (30 python snippet) running on 100 devices:
  - Query Count: 26523
  - Duration: 18s

New Release:
- Workflow with 5 empty python snippet services, 1k target devices
  - DxD: (Normal Mode) 34s - (High Performance Mode) 750ms
  - SxS WT: (Normal Mode) 2s - (High Performance Mode) 600ms
- Update a pool with 10k devices: 110ms / 50k devices: 250ms
- Add 10k devices to a manually defined pool (Add instances in Bulk): 2.2s
- Calls to "save_positions" endpoint in "Large Workflow": 20ms
- Time of Workflow Duplication for "Large Workflow": 140ms
- Large Workflow (30 python snippet) running on 100 devices:
  - Normal Mode:
    - Query Count: 23293
    - Duration: 9s
  - High Performance Mode:
    - Query Count: 184
    - Duration: 120ms

Migration:
- Run migration script to:
  - Convert all devices from type "device" to "generic_device"
  - Convert all links from type "link" to "generic_link"
  - Convert all files from type "file" to "generic_file"
- All custom services must be updated:
  - The job function can become either a classmethod if the function need to use class attributes (see
    Ansible Playbook Service), or a staticmethod (see any other services)
  - All custom services that make database update (e.g using db.fetch, db.factory, device.property = value, etc)
    must be updated to use the session_scope so that the SQLAlchemy session is removed at the end of the
    transaction
- All REST Call Services must be updated:
  - The "payload" property, previously stored as JSON, must be converted to a string with json.dumps
  - The new "substitution_type" must be set to "dict"
- The "migrate" endpoint has been modified with a new mandatory "import_type" argument. All REST calls to "migrate"
  must be updated accordingly.
- Performance optimization of user code in workflows: the new "properties" keyword argument must be used whenever
  "fetch_all" (or "fetch(all_matches=True)") is called and only a subset of properties are needed, so that the workflow
  does not fetch the SQLAlchemy objects
- Update for Netmiko Commands Services: if a service uses a single command, and "Results as list" option is checked, the
  results will now be returned as a list. To preserve backward compatibility, the option must be uncheckd (set to False) in
  the migration files for all netmiko services with a single command, the "Results as list" set to True.
  Note: Update migration script to trim empty lines before setting results_as_list to false
  Commit: c50cee1f1f67b69d8306d6b6d33b377da5f4f350
- In automation.json, change "use_task_queue" to "task_queue" (false or "dramatiq")

Documentation Update:
- Removed extra "Admin Only" property for Credentials (meant to override the "Access Control" admin only ?) If this "Admin Only" property still exists outside of eNMS, it must be added as a deviation.

Tests:
- Test everything about the "Add services to workflow" mechanism (everything has changed, especially the
  Search mechanism)
- Check that all services have a unique persistent ID across all services (mandatory now that results display
  rely on persistent ID instead of ID previously)
- Test the Ansible Playbook Service (exit codes no longer available directly)
- Test Workflow with a superworkflow
- Test running services from the REST API with both devices and pools
- Test that all device connections are properly closed at the end of a run
- Test Parameterized Runs (with and without custom targets)
- Test Restart Run, specifically that new runs can fetch the results from old runs
- Test the "Update Target Pools" mechanism
- Test that the get_result function work like it used to with all possible combinations of parameters
  (with device, without device, with scoped name and full name for the service, with "all_matches" set
  to True and False) regardless of the value of "High Performance"
  The output of "get_result" should be the same regardless of the value of "High Performance"
- Test that the "Report" mechanism works correctly regardless of the value of "High Performance"
- Test the Restart From mechanism, with all possible target origins, with both "High Performance" enabled and disabled
- Test the Ansible Playbook Service
- Test the "update_instance" REST endpoint, specifically the update of a relationship by passing it the names of the
  related model (for example, update the target devices of a service)
- Test that the number of threads allowed depends on whether High Performance is checked or not (* 10)
- Test that the display of an edge in the workflow builder and a link in the network builder is properly updated after
  editing the edge (name or color)
- Test that all relevant forms and tables have the "Last Modified", "Last Modified By" and "Creation Time" properties
- Test that the Netmiko services that uses to have a single line command and "Results as list" checked are still working
  and the result is still returned as a string (because the option as unchecked during migration)
- Tests what happens when dramatiq triggers the same jobs twice (in previous release, logs and results were disappearing because created twice)

Notes:
- Everything in the "Tests" section should be tested with both "High Performance" checked and unchecked
- The "High Performance" flag comes from the superworkflow if there is one.
- Modifying a workflow (updating services, removing or adding edges, etc) will no longer affect on-going runs as the topology is saved before the run begins
- In "High Performance" mode, results cannot be read from the UI until the workflow has completed.
- It is no longer possible to set device attribute from a python snippet or python code by doing
  "device.property = value". The factory function must be used instead:
  "factory("device", name=device.name, property=value)"
- In "High Performance" mode, the "fetch" global function in the workflow builder returns namespaces instead of objects. It can no longer be used to fetch associated objects (e.g "pool.devices")

Version 5.2.0: Data Store and Various Improvements
--------------------------------------------------

- Clean up table filters in the "Files" table when entering a folder (PR)
- Add search mechanism to the session table
  - Make Device.table_properties use the table_properties function from Base class
  - Add new "Session" column to the session table: allows searching through session content
    just like in the Configuration table
  - Add slider to the Session table to select number of lines of context to display
- Store the positions of services in a workflow in the workflow itself, instead of storing
  them at service level. Motivation for the change
  - When exporting a workflow, we are exporting start and end services, including the positions
  of the start and end services in all workflows (not needed)
  - When importing a workflow, we need to merge the positions dictionary of Start and End services
  being imported into the existing ones
- Store the positions of network nodes at network level
- Make workflow link persistent across releases (with a new property "persistent_id" different
  from the database ID and exported in the migration files / generated with urlsafe_b64encode
  so the persistent ID can be safely used in URL)
- Add options for all fields accepting python code to automatically format the code with black.
  Move black to requirements.txt (from requirements_dev.txt)
- Remove "refetch_after_process_fork" option (always refetch after process fork)
- Fix bug when entering enter when searching a property like server_name on a table (e.g worker table)
- Display service color in Workflow Builder and Workflow Tree based on "color" key in the device
  results if it exists
- Workflow Tree updates:
  - Add yellow color to services that match a workflow search in the workflow tree
  - In the workflow search panel, add an option to include all services in the workflow tree:
    - When the option is disabled, services that do not match are filtered out.
    - When the option is enabled, services that do match are highlighted and services
    that don't are displayed normally.
  - In Tree Search, add support for regular expression search
  - Update 'serialized' property to be case sensitive for network and workflow search, and remove the
    relationships from serialized
- When device filtering is enabled, limit results displayed in result table to the filtered device
  (note: device filtering is not compatible with the "Only save failed results" option)
- Fix table form filtering bug: invert checkbox constraint in table filtering not enforced previously
- Upgrade JQuery to the latest version v3.7.1
- Select node in workflow builder from tree left-click selection and allow for multiple selection
  via the tree
- Use full name instead of scoped name in run table
- Add 'name' property to changelog to remove special case in to_dict from bug fix in
  bcdb8cb051d8b0d131a2826da093e3643203e6dd (error 500 when returning an object from the REST API)
  Commit: 1fe9217b0deb4f23ff6546af6d1a290ad44ab10c
- When double-clicking on a service in another workflow in the workflow tree, introduce a 200ms delay
  before zooming on a service in that workflow otherwise the zoom does not occur.
- Fix sqlalchemy warnings about implicitly combining columns ("SAWarning: Implicitly combining column
  device.icon with column network.icon" and same warning for admin_only)
  (email: "gunicorn startup messages")
- Remove "network" from the rbac.json "rbac_models" and make it inherit its RBAC properties from device
- Make the icon default to "network" in the Network form instead of "router"
- Reinstate the log lines in the multithreaded disconnect function at the end of a run. Cache the log_level
  to prevent PendingRollbackError errors (see slack thread)
  Commit: 2b624a314d112388b6974e1cd71e8a972366de18
- Update eslint (and package.json) to work with the latest node.js / eslint version
- Rotate all fa-sitemap icons to 270 degrees with "fa-rotate-270" class, including in the workflow tree
  and the "Add Services" panel
- Refactor credentials to use the RBAC 'Use' section instead of the old 'User Groups'
  - For consistency with the way RBAC work in general (credentials didn't have RBAC before as they were
    "admin only")
  - For consistency with secrets (being allowed to use a secret is controlled via RBAC 'Use')
- Update select2 library to v4.1.0 (the 'Select {model}s' text disappeared after jquery update)
- During workflow duplication, commit once after creating all edges instead of commiting after each
  edge creation to speed up process
  Commit: dcd119a9e7c19ceb2bd786fd8e25419cdfeceaea
- Update to the logs window:
  - Fix wrong spacing after 'Gathering logs for' log in logs window when running a service
    Commit: d847bb39f3f33be684f83f7b7e13215a01d196b3
  - Add a new search feature in the logs window to filter the displayed logs
  - Move logs and report control panel in header so that it stays visible at all times (e.g for searching
  and switching runtimes while autoscroll to bottom is on)
    Commit: fcd6af69afa8ce030ecf1b2a2d639db5f15a5295
  - Add a new 'Autoscroll' feature to the logs window, allowing users to disable automatic scrolling to
  the bottom while logs refresh (to read the logs without being pulled back to the end)
- Fix bug where the in-workflow "fetch" function in runner.py could not work when filtering by
  model because one of the mandatory variable was named model (conflict with model from kwargs)
  Commit: 40be7555172b6da9db2be294cef548d8e28a1ae8
- Update the service neighbors query used in the workflow traversal algorithm to use a SQL query to
  get workflow edges instead of a python generator to speed up workflow execution in DxD mode
  Commit: c79fdbe4f8f5ab84e5944006017cad7e66b23854
- Prevent run.get_state from getting called twice when displaying the workflow tree while a workflow
  is running
  Commit: a4a31cca7a4e87bcf60c74ca9189a956b7385bea
- Don't export soft_deleted relationship objects via "to_dict" to prevent migration import errors
  Commit: fef814960881b48841e4928c5032427769cc8af0
- Force global_delay_factor to 0.1 in update_netmiko_connection function when fast CLI is enabled
  Commit: 03323f1fb46c9d6b8ce1337da552f4f03ed3d7d4
- Update the bulk export feature to export services to the user's browser as a .tgz archive instead
  of exporting them to the server
- Fix refresh dropdown bug in the workflow builder (an active search was only working up until the
  next refresh because we empty and rebuild the dropdown list at each refresh)
  Commit: bcb6bb77e55f938f15b8751853f00158c5849847
- Fast CLI update:
  - Remove fast_cli from all Netmiko services and from the UI
  - Pass fast_cli=False to Netmiko ConnectHandler object
  - Have Global Delay Factor default to 0.1 (for new services)
- Add "version" property in service table (via properties.json)
- Make "controller.filtering" function available in the workflow builder global variables
  - Typical usage: "filtering("device", constraints={"model": "Cisco"})"
  - Allow filtering to be used in the Device Query field to define the targets of a service / workflow
  - Add regression test workflow "Functions: filtering"
- Profiling mechanism:
  - Monitor the performances of each function of the application, specifically:
    - "count": how many times a function has been called
    - "average_time": how long does the function take to execute on average
    - "combined_time": total time spent running the function
  - Add a troubleshooting snippet to display the results for each function, with the ability to filter
    per type (count, average time, or combined time), class (e.g Controller, Environment, Runner, etc)
    and to limit the number of results.
  - Add a troubleshooting snippet to empty the profiling data
  - Add mechanism in admin panel to download the profiling data as .json file
- Fix bug 'Object of type datetime is not JSON serializable' when upadting a local file tracked by the
  "monitor_filesystem" function
  Commit: 3e96705dde1869179f0c3e1997949d13479008e7
- Always consider min refresh rate value when refreshing workflow (previously hardcoded to 5000 in a few
  places such as refreshService)
  Commit: f27898da8fbf25a2cbbb5c9bceb6e68e39b3b5bb
- Fix prettier linting configuration and lint all files with prettier
  Commit: 073c63625995701825d81d97d76aa305bcfa4f9a
- Improve how errors in user code are returned in workflow logs and results
  - In Python Snippet Services: Commit 1215ca90f3cbf2587c8312bf9cb680ef8cf2919f
  - In substitions / eval (python field and "{{ }}" queries): Commit ece3355fd6ebbf08b36547aee6cba72517c820d5
- Set rbac to None in workflow builder "get_all_results" to bypass rbac (PR)
- Add support for Duo Authentication
  - Configuration in settings.json > "authentication" > "duo" (client ID, host, redirect URI)
  - Secret configured via "DUO_SECRET" environment variable
- Add 'Runs' link to run relation table in task table
- Add RBAC to sessions
  - Previously "admin only", sessions are now RBAC controlled ("read" access only)
  - By default, the user initiating a session is set as owner of the session object, and the "Read"
    access field is left empty (no groups)
  - Add an edit button to the session panel to edit RBAC (the other fields are "read only")
- Fix NProgress bug ("done()" called before "start()": loading never ends)
  Commit: 65c0972610f39871f06c5707b540669468bd0844
- Add Jinja2 support to the Netmiko Configuration Service
  - Commit: 4caed99b575aa35b06e7c2e0a6e0ee096e7db81c
  - Add regression workflow "(R) Netmiko Configuration with Jinja2 template"
- Make 'load_known_host_keys' a property in automation.json instead of a service property
  to remove one of the deviations
  - Property can be configured in automation.json > "file_transfer" > "load_known_host_keys" (default: false)
  - Commit: 577f16d1830c7dba1c94e4f3285faa74d0319051
- Improve deletion message in builder to distinguish services/devices and labels
  Commit: 06b4c8057da254a30f55685fcb03fd4e8fff62a4
- Update "Copy to Clipboard" mechanism in File Table to copy relative path instead of full path
  Commit: 152a1bcf7dcab8f3a12c0702b9c33677efef7217
- Add substitution mechanism to the Git Service 'commit_message' property
  Commit: 43367981162d2719bb4dc4fadc19fc6ea5342b0e
- Make service column in task table a hyperlink to the workflow builder (when applicable)
- Replace 'n°' with '#' for numbering fetch, commit, and retry operations
- Prevent saving the pool form if it contains an invalid regex
  Commit: 37d5cb64738dffd5d698ba4f8a07e84e262d2a51
- Add new "creation_time" property for the following models: device, link, pool, service, user, credential,
  file, secret, group, task
  Commit: 6a750a008e28b5dae68da04fbe549a771c0ac8a5
- Add new "notification" key in automation.json to configure which notification mechanisms
  are available in Step 4 of the service panel, as well as in the drop-down list of service
  types in the Workflow Builder and Service Table
  Commit: 86a5f40dafb4bc08fe8a171ff4f8b236506a13b3
- Enable the "run_service" endpoint in the REST API to support using Persistent ID instead of name
  so that REST calls don't break if the service name changes.
  Commit: 8260e0954647c8283b335bdf9dcfb4b2c6e5f91c
- Prevent a user from setting a workflow to be its own superworkflow.
  Commit: f44001a8642f59e2085ce440204a65d435b2ab4a
- Remove hyperlink for single object select list (panel would pop up unexpectedly)
  Commit: a8fa8adb875fbdaf373f48bccdee078d81e1f5b3
- In the workflow builder drop-down list of runtimes:
  - Update the refresh mechanism so that an active search in the runtime drop down list
    is still considered after refresh
  - Restore the scroll positition is maintained after triggering the active search
    with trigger('input')
  Commit: 9f29eab326616b1c63c27e3c9604bcd3f29a393e
- Add "runtime" (the parent runtime) to the list of available variables when running
  a workflow ("global_variables" function)
  Commit: 25435861f72ff7f6e7259daacd8ba80a8f47c311
- Make Service Logs and Service Reports available via the REST API
  Commit: dc7d3195b85a03d92532c4844cac9f04a2bce169
- Add new "Show User Logs" option in the service panel (step 1) to only display the logs that
  are user defined (logs that come from the global "log" function available in python fields),
  regardless of their actual log level
- Don't update the "Last Scheduled By" property of a task when it is paused and resumed by an admin
  user (e.g., for maintenance):
    - Prevent the original scheduler's permissions from being affected
    - The changelog should still display that the task was paused and resumed by the admin user
  Commit: 84b3cc6de47253310704d0c2db6f460a510ad72e
- Add information about the sending server in all notifications to quickly identify
  which server is sending the notification (IP address, name, URL, and role)
  Commit: 9c01f4eb0f19cdc7684225d9a3c1579aefea0e2b
- Fix duplicate 'STARTING' / 'FINISHED' logs in workflow logs when multiprocessing is enabled
  Commit: 83fdd0c128a3488b7845d474bd609bd004fa7adb
- Update to the changelog table
  - Make 'author' and 'severity' properties orderable (3436cc545594b4e9379219cf5651170a8acff892)
  - Add new 'Revertible' boolean property (af0886d0df5f1c807b353d4f191d8ee9faeddeac)
  - Add git diff panel for changelog that describes an object update (with non-empty "history" dict)
- Display the network/workflow tree by default if it was previously activated.
  The setting is stored in the database and used to automatically show the tree in the HTML template.
  Commit: 0513847d23e9bfd31fbfd22cdfe9137faf5de6a0
- Added new Data Store feature:
  - A new "Data Store" page in the inventory menu.
  - "Data" is a new model for storing various types of information (e.g., text, secret values,
    JSON objects, - spreadsheets, and DCIM/IPAM data like IP addresses, VLANs, cables, etc.).
  - A "secret," as defined in the previous version, is now a subclass of Data. Secrets must
    be migrated using the data.yml migration file (secret.yml no longer exists).
  - New models can be added as needed: to add a model, create a subclass of Data with custom properties.
    The Python file should be placed in the "models/datastore" folder, and the associated UI table
    should be defined in JavaScript within the "static/datastore" folder.
  - A "Store" is a model designed to contain data. Each store has a "data_type" property that specifies
    the type of data it holds (e.g., a store for IP addresses will only contain IP addresses).
  - A "Store" is also a subclass of Data and can contain other stores (if its data_type is set to
    "store"), similar to how a folder can contain subfolders.
  - The Data Type of a Store can only be selected at creation time. The Data Type of an existing Store
    is set to read-only in the form.
  - The Store of a Data can be modified, but only to a Store of the same Data Type (for example, a
    data of type "A" can only have a store whose Data Type is set to "A")
  - Navigating the data store is similar to navigating files: the current path of stores is displayed
    as a sequence of hyperlinks, each linking to a store in the path.
  - Add new persistent ID to all data types so that data can be seamlessly referenced within
    workflows across releases. The persistent ID can be copied to the clipboard using a button
    in the data store table.
  - Add new JSON object type, with a "value" property to store the JSON object:
    - the JSON object can be edited from the edit panel
    - the JSON object can be downloaded as a JSON file from the JSON table
  - Implement "Get Next in Sequence" mechanism:
      - Add a new "layout" keyword argument to customize the layout of a field, such as adding a button
        to the left or right side of a specific field in the edit panel.
      - Provide an example using the VLAN class: add a button next to the "VLAN ID" field in the form that
        auto-fills the field with the next available VLAN ID when clicked.
  - Implement various models to demonstrate different implementations:
    - VLAN model to show a "Get Next in Sequence" mechanism.
    - Port model to show a SQL relationship with an internal eNMS model ("Device").
    - Cable model to show SQL relationships with a custom Datastore model ("Port").
  - Add "get_data" global function in the workflow builder to retrieve a data in python, either
    by its path or by its persistent ID
- Update to the REST API "update" POST endoint: commit and call the post_update function after the 
  instances have been created or updated (e.g compute pool, update service / file / datastore path, etc)
  Commit: aa9d56c25b5b411195e12da70ffbc637a3765ff2
- Fix worker deletion mechanism (kill process and log message in case or error)
  Commit: e6bf0506aea88f3a5c43bc00fdd59bae2decfbfb
- Add new 'admin_only_bypass' mechanism in rbac.json and rbac_filter to ignore 'admin_only' flag
  for specific properties and models (mainly Credential 'use' section)
  Commit: 3cd8743e2a02646ccda276c34ad49b185a08f42a
- Add 'last_success' property for the configuration backup services

Migration
- Run the script to collect all services position and store them in workflows, and do the same for
  nodes and networks
- Run the script to convert credential "groups" property into "rbac_use" (can be done manually by renaming
  "groups" -> "rbac_use" in credential.yaml too)
- Migrate secrets from secret.yaml to data.yaml

Version 5.1.0: Changelog & Workflow Tree
----------------------------------------

- Changelog feature:
  - Add changelog mechanism for credentials, devices, files, groups, links, networks, pools
    servers, services, tasks and users.
  - Add "Target Type" and "Target Name" properties in changelog table
  - Add revert mechanism to undo the changes in a changelog. Supported revert action:
    - Creation of an instance
    - Standard properties (string, integer, list)
    - Scalar relationships
    - Many-to-many relationships
    - Soft Deletion for non-shared services and edges in Workflow Builder
  - Add changelog support in workflow builder.
    - The changelog of a workflow includes
      - the changes to the workflow itself
      - the changes to any service in that workflow (including services in subworkflows, etc)
      - adding, editing and deleting labels
      - adding and removing services and workflow edges
    - The changelog of a workflow does not include:
      - changes made to the parent workflow (by design)
      - changes made to the superworkflow when displaying changelogs of the top-level
        workflow (not supported)
    - Add changelog button in workflow builder, service and global RC menus.
      When a selection is active, the changelog entry will only display changelogs for
      the subset of services that are selected (similar to skip mechanism).
  - Add changelog button to all tables to display:
    - all changelogs about a specific type of object in table controls (e.g. all device changelogs)
    - all changes about a specific object via link to "Changelog" relation table in every row
  - Add changelog support in network builder
  - Add script (snippet) to permanently delete all soft-deleted edges and services
  - Add option in the admin panel / REST API to delete all soft-deleted services and workflow edges
    older than a given date
  - Require "edit" access for a user to be able to revert a change to an object
  - A changelog must have an "author" to be reverted (system changes cannot be reverted)
- Fail netmiko and scrapli commands service if undefined variable in Jinja2 template
- Make "any" come last in the list of credential type for a service (default becomes read write)
- Dont validate model, vendor and OS for device and link forms
- Add runtime display mechanism (Personal or All Runtimes) to Run table (Results page).
  - Display value is stored in localStorage
  - It applies to both the run table and the workflow builder
  - Add Search field to the runtime list to allow per user runtime search
- Add new user filtering mechanism (per user / all users) for tasks and services
- Add new "start / end query monitoring" python snippet to analyze what SQL queries are sent
  to the database and how long they take to execute (only active in "debug" mode)
- Connection Threshold:
  - Add number of connections for each library in the workflow builder
  - Add new connection threshold mechanism with the following parameters in automation.json:
    - "enforce_threshold": activates threshold mechanism (default: false)
    - "threshold": maximum number of connection (default: 100)
    - "log_level": log level of the warning (default: warning)
    - "raise_exception": prevents new connections from being created when reaching
      the threshold
- Add a way to get the parameterized form to display a drop down of devices with custom set
  of constraints for both InstanceField and MultipleInstanceField
- Move "Admin Only" check box into "Access Control" panel:
  - prevent non-admin users from changing the "Admin Only" value
  - extend "Admin Only" mechanism to all rbac models (plus the group model)
- Add support for named credential in the web SSH connection to a device
- Performance Improvements:
  - Dont inject context processor variables for forms
  - Refactor "get" controller function to only use form properties when serializing object
  - Use flask_caching to cache parts of the Jinja2 templates with fragment caching
    - Full caching for the forms with token post update
    - Fragment caching for the base template (page content + JS variables)
    - Cache configuration defined in settings.json > "cache"
- Add lower menu bar to display profile, server, server time and logout
- Add "Hide Menu" button in upper bar to hide the menu
- Add new global service Search mechanism:
  - Whenever a service is saved, it is serialized and saved as a string in the database
  - The "serialized" property can be used for searching in the service table and in the
    workflow builder
- Add Workflow Tree mechanism
  - New "tree" icon to display / hide the workflow tree
  - The tree is only refreshed when it is being displayed
  - When double-clicking on a service in the workflow tree:
    - If the service is in another workflow, automatically switch to that workflow
    - Automatically select and focus the view on that service
  - When a workflow has a superworkflow, display the superworkflow as part of the tree
  - Track the workflow currently being displayed:
    - Only the tree node on the path of the displayed workflow are open by default
    - The workflow currently displayed is highlighted in blue in the tree
- Skip mechanism improvement:
  - Don't allow skipping Start, End, and Placeholder services
  - When unskipping a service, pop from service.skip dictionary instead of setting to False
    to avoid storing unused data.
- Internal Refactoring:
  - Remove internal "dualize" function as wtforms now accepts a list of values as SelectField
  or SelectMultipleField choices.
  - Refactor internal "to_dict" function from the Base model: add include_relations,
  exclude_relations, and use include for get_properties instead
  - Remove "serialized" @property in base class and make explicit calls to_dict instead
  - Use "class_type" instead of "type" to ignore "dont_serialized" properties in get_properties
  - Remove the "Node" class and merge it with the "Device" class instead. The "Network"
    class now inherits from "Device" the same way "Workflow" inherits from "Service".
    Related issue: #400
  - Networks being devices, they can now be part of pools.
- Add new "Include Networks" property to pools to decide whether the devices of a pool
  should consider networks.
- Add new "source" property to trace the origin of a change: 'REST API', 'Edit Panel',
  or 'Change Reverted'
- Rename the "Undo" mechanism to "Revert" mechanism (given that we're not keeping track of
  a timeline of changes)
- Make device, link and service form "description" field a multiline field
- Add "description" field to the service table (hidden by default)
- Add new "Search" button in the Network Builder: similar to the Workflow Builder search
  without the canvas highlight and per-device filtering
- Extend new "Global Search" mechanism to devices for table and Network Builder search
- Add "is_async" property to the Run class (+ associated column in Results table)
- Add mechanism to automatically hard delete a soft-deleted edge when creating
  a new one with the same parameters. For services, no automatic deletion of soft-deleted
  objects.
- Make non shared services in the service table a link to the workflow that contains them
- Use 'user' instead of 'username' in database functions to avoid conflict with credential.username property
- Make credential type in service form (any, read-only or read-write) come from automation.json,
  under "credential_type" key
- Add new runtime notes mechanism in the workflow builder
  - New "set_note" and "remote_note" global function taking the positions "x", "y" and the
  content of the label as arguments
  - New entry in the right-click menu "Reference" > "Position"
  - A note that is not deleted will be displayed in the workflow builder when the runtime is
  selected, even after the workflow completes
- Extend the per-device filtering mechanism in the workflow builder to also apply to the tree
- Raise RBAC error when no current_user available, "rbac" is not set to "None" and no
  "username" is passed to the function.
- Don't raise an exception in a git service configured to "git add and commit" if there isn't
  anything to commit (add log explaining that there was nothing to commit)
- Export "server" model in migration files
- Add "trigger" variable to the global variables of a run
- Add Dry Run Mechanism:
  - The "Dry Run" is a property of a service (any service, not just the connection services)
  available in Step 1 - part 3.
  - The results of a service in Dry Run mode contains the properties of the service that
  are affected by the substitution mechanism
  - The global variables contain a new "dry_run" property in order to determine in python
  (e.g. preprocessing, post-processing, python snippet service) whether the service is
  currently running in Dry Run mode or not
  - A workflow also has a "Dry Run" property: when turned on, everything inside the workflow
    (including subworkflows) will be considered as running in dry run mode
  - Add support for using "Dry Run" mode from the parameterized form
  - Add special color for services in "Dry Run" mode:
    - In "Normal display": whether the "Dry Run" mode is enabled for a service
    - In "Runtime display": whether the "Dry Run" mode was enabled when it ran
- Activate multiprocessing logging handlers
- Add default / dark theme button switch in upper menu
- Remove dicttoxml (unused), psutil (unused) and itsdangerous (no longer pinned) from requirements.txt
- Add new MediumString column type and make service name a MediumString to allow for longer service (full) names
- Update Show Git History button tooltip from "Historic" to "Historical"
- Add new freeform "version" property in the service class and form (edit panel step 1)
- Unpin ruamel version:
  - Add quotes as "default_style"
  - Add custom representer to fix bug where line are broken inside a return carriage (\r...\n): all strings
    that contain a line break are now treated as a literal block.
  - Preserve order in object properties (OrderedDict) and relationships (sorted)
  - Forbid references (e.g. &id000) in yaml files with representer.ignore_aliases to avoid change of id number
  - Refactor get_yaml_instance to use the "typ='safe'" keyword because of database corruption issue by ruamel
    when it isn't used
  - Add a representer for tuples because service positions can be stored in the database as a tuple
  - Move 'get_yaml_function' in custom app to allow for custom representers / constructors
- In the Netmiko Configuration Service, return the netmiko send_config_set output under "result" key, and the
  actual configuration under "commands" key for consistency with other services
- Refactor the allowed controller endpoints in the REST API to come from rbac.json (previously hardcoded
  in rest_api.py)
- Refactor 'add_instances_in_bulk' endpoint to make it available from the REST API. Example Payload:
  {
    "target_type": "service",
    "target_name": "service_name",
    "property": "target_devices",
    "model": "device",
    "names": "name1,name2"
  }
- When initializing the app, only consider the JSON files in the "setup" folder (otherwise, temporary
  files like *.json.swap files created by vim prevent the app from starting with JSON load exception)
- Add "cmd_verify" Netmiko parameter to the Netmiko Configuration Service
- Add "read_timeout_override" Netmiko parameter to all Netmiko services
- Before setting a run status to "Aborted (RELOAD)" when the app restarts, check whether the run has a
  valid process associated to it and don't do anything if it does: this allows for individual process restart
- Refactor the Unix Command Service "Approved by an Admin user" mechanism:
  - Before, the approval was only required to change the command itself. Editing the service without changing
  the command would not require re-approval.
  - Now, anytime a Unix Command service is edited / duplicated by a non-admin user, the service must
  be re-approved.
    - When a non-admin user is doing the edit via the edit panel, the "Approved by admin" check box
    must be unchecked to validate the form.
    - When deep copying a Unix Command service into a workflow, that property will be silently unchecked.
- Add mechanism to refetch run objects (such as service, placeholder, etc) after process fork when using
  multiprocessing. Can be deactivated in automation.json > "advanced" > "refetch_after_process_fork"
- Add support for connecting to multiple LDAP servers:
  - Default behavior is unchanged: the app looks for the LDAP_ADDR environment variable and initializes
    a single LDAP servers
  - If that variable is not set, the app looks for the "servers" key in
    settings.json > "authentication" > "methods" > "ldap". Servers is a dict that associates LDAP server
    IP/URL to its keyword parameters (see ldap3 python libraries)
- Fix bug that prevented uploading files to a folder when the folder name starts with a number (e.g. "1test")
- Use "class" key in handler config in logging.json to have the same syntax regardless of whether
  "use_multiprocessing_handlers" is set to true or false
- Allow custom subject for emails (in email notification - step 4). If the subject is left empty, it defaults
  to the current subject (PASS/FAIL + service name)
- Remove "Bulk Deletion" button from the session table
- Fix cascade deletion of results objects when the associated device is deleted (missing
  backref cascade deletion: 58370667b723bbdb0f8f50f931bad8a4586d172c)
- Make current_user available in parameterized form as "user" variable
- Add parent_runtime constraint in REST API get_result query to fix performance issue
- Add run cascade deletion when deleting a service (in rbac.json)
- Fix connection with non-default name not closed at the end of a workflow bug
  Commit: c9b164bd35732e9f54d0bb46c6bff61631ab85f4
- Add quotes around ansible playbook service extra_args argument
- Fix Netmiko File Transfer Service missing netmiko_timeout_override property bug
- Fix Unix Shell Script Service missing netmiko_timeout_override property bug
- Move 'close_remaining_connections' at the end of run cleanup so it does not impact the result creation
  in case of failure
- Add an optional "runtime" parameter to the workflow builder's "get_result" function to retrieve results
  from a run different than the ongoing run
- Add ordering mechanism for instance fields and multiple instance fields, with the following syntax:
  x = (Multiple)InstanceField(..., order={"property": "name", "direction": "desc"}
- Name of current thread when running a service no longer set to runtime
- Add mechanism for optional search box in table 'column-display' dropdown list
  - Syntax: add "{ search: true }" as argument when calling "columnDisplay"
  - Add search box by default to device and configuration tables
- Force downloading file to browser by adding "as_attachment=True" option in flask send_file function
- Change 'Skip' label and tooltip to 'Skip / Unskip' in workflow builder
- Move "state" commit in the end of run cleanup after trying to close all remaining connections to get an
  accurate display of the number of remaining connections.
- Re-add logging lines from disconnect function that were removed because of transaction issue after end of
  transaction commit: use cache mechanism in run.log function (a098e2b62f7a46d2c8d0fc2a3e6ad6fddcf9b847)
- Add new log truncate mechanism, configured in automation.json > "advanced" > "truncate_logs" via the keys
  "activate" (truncate or don't truncate) and "maximum_size" (default: 200000000)
- Rename automation.json > "advanced" > "always_commit_result" to "always_commit"
- Add automation.json > "netmiko" > "connection_args" option to pass additional parameters to netmiko
  ConnectHandler class
- Add optional "SSH_URL" environment variable to define URL used for the webSSH connection to devices
- Add new settings.json options for custom branding:
  - "app" > "name": defines window name + app name displayed in the upper left corner + login page name
  - "app" > "theme": default theme used during user creation and switching back from dark mode
- Add new "memory_size" property for the result class that shows how much memory a result takes in database.
- Add new "memory_size" property for a run class that shows how much memory a run takes in database.
  This number is the sum of the size (obtained via "getsizeof") of all results and all logs saved to
  the database during the run
- Remove "Save" button in server panel when accessed from left side menu lower bar
- Add log obfuscation feature: if an input field uses either get_secret or get_credential, it must be obfuscated
  in the logs and results. Otherwise, it appears as it is after substitution.
- Add runtime name and search box in logs, report and results panel
- Don't let non-admin users change admin only RBAC property
- Don't fetch credential object and dont add secret to credential dict in rest call service using custom credentials
- Update to the workflow refresh mechanism:
  - Move the refresh setTimeout inside the callback function to avoid stacking refresh
  - Compute refresh time based on how long get_service_state endpoints takes
  - Update the refresh timer for individual service refresh to 5s
  - Add new parameters in automation.json / "workflow" / "builder_refresh_rate" to configure
    min, max and factor used to compute refresh rate based on elapsed time
- Add new settings "allow_file_deletion" in settings.json / "files" to explicitly allow deleting local files that
  are located in the trash folder. Set to false by default.
- Defer Service.positions to improve run performance
- Always set the positions as a list instead of a tuple to remove the need for a specific constructor
  for tuples in the migration files
- Exclude Start and End services from the changelog table when displaying the changeog of a workflow
  Commit: d757ae648df5529a699567e370ebcfcebeb43307

Deviations:
- Deviation 1 (5f51ad98c843f776c46c42faf3fe904b02bc37fd): Database.configure_events service subclass check: 
  Updated from original deviation to include "service_report" along with "service_log"
- Deviation 2 (a079abb60069821d284fb2d36b65685b8852f054): Controller.import_services try deleting the service
  folder before extracting the archive
  No change from original deviation
- Deviation 3 (c36d96ef702b6c2b08c7f67b5490a712d001cd8a): Controller.update_database_configurations_from_git
  commit after each device update instead of committing once for all devices
  No change from original deviation
- Deviation 4 (396b64b789b2b7b4c6afc3a4c2d7fa7549c8573d): Database._initialize change error message when
  failing metadata creation
  Updated from original deviation to include process ID in error message
- Deviation 5: Database._initialize commit/rollback deletion of workers when initializing database
  Updated from original deviation to include additional commit in server update + minor refactoring
- Deviation 6:
  - Add custom function decorator to call a function from CustomApp whenever it exists
  - Use "detect_cli" function from CustomApp if defined there
  - Use "init_dramatiq" function from CustomApp if defined there
  - Use "init_redis" function from CustomApp if defined there
  Could not make retry mechanism work because of internal redis error:
  "AttributeError: 'Retry' object has no attribute 'update_supported_errors'"
  - Add "init_vault_client" retry mechanism:
    - 65def692961c4bff8565e0537cddbb2ca902ad5b
    - 07238606e7ac53c18eca115f9ba14f8c3851c5b5
  - Use "init_vault_client" function from CustomApp if defined there
- Deviation 7 (d54165d2eb072c962006a47189beb2e5536c7c8d): dont run filesystem monitoring when CLI detected:
  add new Environment._initialize function to avoid circular import issues now that detect_cli is in custom.py
- Deviation 8 (001ac08fc1225272382b214a6e687b313249b142): use vs.logging instead of opening logging.json
  in Environment.init_logs
  Partial merge of original deviation: no deepcopy of logging config
- Deviation 9 (912ce3c125a4c7b7d6c253eb2313404ef10a9046): add log_post_processing for custom environment log mechanism
- Deviation 10 (f23785dcd122466b4509763e11622155cbbc86ce): replace 'standby' with 'secondary' iin forms.py Server.role
- Deviation 11: parameterized form context help (merged PR)
- Deviation 12 42d305763d0bb20ef103ea6cfbb7d7f7c5a99c0c: move rest endpoints from RestApi class to rbac.json
  to handle custom endpoints
- Deviation 13 (76a4e9ba3ae19cc60fc426bc901d3b56615a36ff): add try/except when doing recovery and result/log
  creation of 'Running' run after app restart: log traceback and runtime if it fails
  Partial merge of original deviation: changed log error message
- Deviation 14 (68cf6cc3d338602c92170cb09f0b34dab1fd2185): add try/except around close_remaining_connections
- Deviation 15 (a43b9c4985ce85a9da8a353014056b87782f86f6 ): add logs truncate mechanism (not active by default)
  Partial merge of original deviation, see commit and release notes above
- Deviation 16 (d0b40b1e84f85258d556eae533fd1930548a1d16): commit in generate_report function if 'always_commit'
  option is set to true in automation.json and rename automation.json > "advanced" > "always_commit_result"
  to "always_commit"
  Partial merge of original deviation: optional instead of commit=True
- Deviation 17 (594e97cd812d802959d79006bfb2db376fe0112b): add 'runner_global_variables' function in custom app
  to add custom variables to global variables used in a run
- Deviation 18 (e78db1cc93b4625e76996d015ad8aeb83b219163): add new dictionary in automation.json >
  "netmiko" > "connection_args" used to pass additional parameters to Netmiko CustomHandler class
  Partial merge of original deviation
- Deviation 19 (dcaa5b4b40abe8bcaf2b83820920efd082e05746): ssh_url / sshUrl to define url for webssh connection
  to device
- Deviation 20 (e5b3171ac34c9dcaaad23819f9594c74fab1288f): add method to inject new variables in flask template context
- Deviation 21 (c24dabda29aca680a6305a2df7062a9fec3a4cf1): add missing cascade deletions for service log class
- Deviation 22 (f7f722f957f5d3172fd9b0f642ae5d4983799442): vault __getattribute__ function add try/except mechanism
  Partial merge of original deviation: only catching the exception but not raising it. Default to an empty string
  in case of exception
- Deviation 23 (594dc6f8404e3b92567432549514effcfcbfbba4): add netmiko command verify property to netmiko prompt service
  Partial merge of original deviation: added as property instead of hardcoding it to False
- Deviation 24 (123c3061801bed977b7316611d8a7d15b38bbb05): use try_commit in the compute pool function
  Different from original deviation (explicit try/commit except/rollback one time)
- Deviation 25: custom branding (see release notes above)
  Partial merge of original deviation

Migration:
- network.yaml must be merge into device.yaml:
  - replace "nodes" with "devices"
  - remove all the "positions" key
  - copy/paste the content of network.yaml in device.yaml
- Add quotes around all values in metadata.yaml
- Update rbac.json with the "allowed_rest_endpoints" variable
- Import the migration files in the new version:
  - Remove the typ="safe" keyword in the "get_yaml_instance" function in custom.py
  - Start the application and import the migration files from the last release
  - Stop the application and re-add the typ="safe" keyword to the code
  - Start the application and Export the migration files
  - Drop the database and Import the migration files again (that were exported in the last step)

Version 5.0: Clustering
-----------------------

- Add new Clustering menu entry with "Server" and "Worker" pages
- Add one-to-many relationship between Run and Server class
- Add one-to-many relationship between Worker and Server class
- Display server and worker in run table as hyperlink to the edit panel
- In Server SQL table and Server table in the UI:
  - Add "scheduler_address" and "scheduler_active" properties in Server table. These properties
    are initialized with the SCHEDULER_ADDR and SCHEDULER_ACTIVE environment variable.
  - Add "runs" and "workers" links in server table
  - Add "version" and "commit SHA" properties
  - Add "location" property, populated from SERVER_LOCATION environment variable
  - Add "Last Restart" property in server table: updated every time the application starts.
  - Add "Current runs" property in server table: counts number of runs currently running on server.
  - Add "Role" property to distinguish between "primary" and "standby" in the cluster
  - Add "Allowed Automation" property to control allowed automation:
    - "scheduler": server can run jobs from scheduler via "run_task" REST endpoint
    - "rest_api": server can run jobs from REST API via "run_service" REST endpoint
    - "application": server can run jobs from the UI via "run_service" controller endpoint
  - "Allowed Automation" can be configured from settings.json > "cluster" > "allowed_automation"
- Rename 'import_version' key to 'version' in settings.json > app
- Update both server version and commit SHA every time the application starts
- Add server version and commit SHA at the time of the run in Run table as string properties:
  - These properties are not updated when the server version / commit SHA is modified
  - These properties are not erased if the server object of the run is deleted
- Add new "Worker" table in database and UI (Administration menu)
  - A worker is created or updated whenever a job starts running
  - The worker name is built as server name + process ID to guarantee that it is unique
    across servers
  - Add "process_id" property (populated with getpid())
  - Add "subtype" based on the "_" environment variable (e.g. python, gunicorn, dramatiq)
  - Add "last_update" property to show when the worker was last used / updated
  - Add "server" hyperlink to the edit panel of worker's server
  - Add "current_runs" property to show how many jobs the worker is currently running
  - Add "runs" property: one-to-many relationship between worker <-> runs, and button in
    worker table to display all runs executed by the worker.
- When loading the application, check whether the server's workers are running and if not,
  delete them from the database
- Workers are created when they are detected by the application, ie when a service is run
  by the worker
- Refactor get_workers REST endpoint to use workers in the database instead of storing
  worker data in the redis queue
- When a worker is deleted from the worker table, send SIGTERM signal to underlying process
- Don't check for metadata version when doing migration import, only check for service import
- Add mechanism to use a StringField for the properties in properties.json > "property_list":
  - if the list is empty, will default to StringField instead of a SelectField.
  - new format in case of a SelectField: must provide all wtforms keyword arguments
- Add mechanism to compare configuration properties between two devices:
  - New drop-down list in configuration table to choose configuration property
  - New "v1" and "v2" column to choose which devices to compare
- Add setting to control whether or not to monitor changes system in
  settings.json > "files" > "monitor_filesystem"
- Add new "name" field to the "Parameters" class so it can be updated from the REST API
- Add support for BCC in the send email mechanism (service step 4 and email notification service)
- Add new "Secrets" mechanism for the user to associate a secret value to a key, and decide via
  RBAC which users can view, edit and use them in a workflow.
- Make 'runtime' property of Run class unique at database level ("unique = True")
- Add new "Sender" field for the email notification mechanism (service Step 4)
- Add new snippet to delete corrupted services ("delete_corrupted_services.py")
- Make pool 'fast compute' mechanism optional via new "pool" > "fast_compute" boolean
  property in settings.json (default: true)
- Add new try_set function to retry updating a property in case of deadlock
- Add new key in automation.json: "advanced" > "always_commit_result" set to False by default.
  If set to True, results are always committed as soon as they are created to avoid deadlocks.
- Refactor "service run count" mechanism to work with the redis queue and correctly update
  the service status ("Idle" / "Running") at the end of the run
- Refactor netmiko backup service and scrapli backup service to retry the configuration
  update transaction in case of deadlocks
- Forbid redirecting outside of the base URL in the login redirection mechanism
- Prevent active HTML / JavaScript in the cells of a table by default, and add the `html`
  keyword in properties.json to allow it wherever necessary.
- Add `sanitize` function to sanitize user input in the HTML-enabled cells of a table
- Validate that the path of a file is inside the "files" folder when renaming a file object
  or uploading a file.
- Move v1/v2 in config table after the configuration properties columns
- Move v1/v2 in all results table before the table buttons
- Add runtime in traceback when a run fails in controller.run function
- Add try_set and try_commit to run global variables
- Add new timeout when trying to close connection with multithreading. Timeout is configured
  under automation.json > "advanced" > "disconnect_thread_timeout" (default: 10s)
- Append 3-digits postfix to all runtimes to prevent name and runtime collisions for
  runs that start at the same time (replaces jitter mechanism)
- Refactor the end of run transaction and cleanup mechanism after a run is interrupted by
  a critical exception or application reload:
  - Trigger end of run transaction to have results and logs available
  - Remove the run data from the redis queue (if a redis queue is used)
  - Close connections to device (in case of an interruption by critical exception)
- Make the value of a Secret a private property
- Major logging update to prevent stuck workflow with dramatiq processes > 2:
  - Add support for multiprocessing capable logging handlers
  - New "use_multiprocessing_handlers" key in logging.json to decide whether to use
  the multiprocessing capable logging handlers

Migration:
- Update properties.json > "properly_list" with new format

Version 4.5.0: Custom Parameterized Form, Bulk Filtering & File Management
--------------------------------------------------------------------------

- Bulk Filtering mechanism
  - refactoring of the service template with new Jinja2 macro
  - Existing caveats:
    - Cannot filter service type or device type specific properties
    - Cannot be used for bulk editing
- Round result size to 1 decimal when the result size is higher than 50% the maximum
  allowed size
- Don't allow saving a workflow if the run method is set to Service x Service and the
  workflow has target devices, pools, or a device query
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
- Remove pin to 3.4 for netmiko (move to netmiko 4+)
  - remove delay_factor and add read_timeout property.
- Fix duplicated run name when running a service from the REST API bug
- Order model drop down lists in the UI based on pretty name instead of tablename
- Add user "last login" property (record time of latest login)
  Commit: f2e4f2658ae0157020412684226e2a1a8cb58aa2
- Add zoom sensitivity control in user profile for Workflow Builder
- Remove "username" variable from workflow global variables and add "user"
  dictionary instead with name and email. Mandatory checks:
  - wherever "username" is used, it must be replaced with user["name"]
  - "user" must not be used in existing workflows
- Add new "ignore_invalid_targets" parameter in run_service REST endpoint to run
  even if there are invalid targets.
- Update size of restart workflow from panel to fit to content
- Add device name to git history comparison panel title
- Add task name, target devices and target pools to the run table ("Results" page)
- Add custom parameterized form feature:
  - new "Parameterized Form Template" field in service panel > step 1 for the HTML code
  - supports JavaScript code inside <script></script> tag
  - must follow the same template as the default parameterized form ("form_type" variable,
  add-id / btn-id CSS class, eNMS.automation.submitInitialForm run function, etc...)
- Improve performances of migration import mechanism (~ x10)
  - Use CLoader to load migration files
  - Use a dictionary to store SQLAlchemy objects so that they are only fetched once
  - Disable log events during import
  - Commit: 9d2ceaee0784b25e203ac09ad44c38deab56a4e0 / 6fb025f981216de05b3db83b1912645a5dc60f59
- Add "Last Run" property for services to indicate the last time it was run
- Revert update function default RBAC value back to "edit". For relationship update, required
  "read" access instead of "edit" access (7342db9e4261e8fbbed34e938c58b13943dff54d)
- Reduce number of fetch when running a workflow:
  - number of fetch / 10, execution time improved by 30%
  - lazy join of run.service, workflow.services / edges, workflow edge source/destination/workflow
  - new device store in workflow job function to avoid fetching devices multiple times
  - Commit: b56feea372d852f3613b62d029b130e16c226a33
- Dont include payload in intermediate workflow results (1ae5a7b25a53d5ab00527fe7bb3e682cc6853fda)
- Add string substitution support in the mail notification service fields (sender, recipients, reply-to)
- Dont allow enabling multiprocessing if the run method is not set to per device
- Remove password from netmiko connection object after opening connection
- Add metadata file when doing migration or service import / export
  - metadata includes export time, export version, and service name in case of service export
  - fix shared workflow import bug (empty list => no way to detect main workflow)
  - in settings.json, add new "import_version" to disallow importing older files (if the
  version in the metadata is not the one from settings.json, the import fails)
- Reduce number of fetch in the scan_folder function to improve performance
- Refactor get_workflow_results to speed up workflow results display
- Refactor get_runtimes to no longer query the result table
- Skip bug fix for run once service (from thread: "Skip query not respected")
  Fix: if a "run once" service has targets and all targets are skipped, then
  the service is not run.
- Make Result.service_id and Result.parent_runtime indices to speed up results display (filtering/result)
- Add "SETUP_DIR" environment variable to set path to folder where json settings files are located
- Add new "migration" key in setup.json > paths to set path to the folder where migration files
  are located
- Dont update configuration properties if no change detected:
  - Commit: 58798c182c4c61f53b943bb487d16688c225366e
  - in backup service, don't write to local file, don't update value in database and don't
  update "update" timestamp if the value hasn't changed
  - in the "update database configuration from git", dont update the database configuration
    if the "update" timestamp from git is the same as or older than the one stored in the database.
  - Add "force_update" argument to "get git content" and "update database configuration
  from git" functions (when the app runs for the first time, this argument is set to True)
- Add parameterized form properties in dedicated accordion in service edit panel
- Display header and link before results in email notification
- Files Improvements:
  - Refactor the files mechanism to no longer display the full Unix path, only the path
    from the files folder
    - "files" displayed as breadcrumb even if the actual path does not include such a folder
    - the copy to clipboard mechanism still returns the full path so it can be used in e.g. python scripts
    - allow both absolute and relative paths in generic and netmiko file transfer services
    - impact on migration: all paths in files must be truncated by removing the path
    to the "files" folder
  - Prevent uploading the same file twice in the file upload panel (or another file
    with the same name)
  - Add trash mechanism for files. Two options:
    - 1) Put trash outside of files folder (not tracked by eNMS). When deleting a file, the database
    object is deleted and the associated unix file is moved to the trash folder, with the current
    time as prefix.
    - 2) Put trash inside the files folder: the same mechanism applies, but the trash folder is
    being tracked by eNMS. Files can be restored (by moving them from the trash folder to another
    directory), and whenever a file in the trash folder is deleted, it is removed (rm) from the
    filesystem. Files are moved to trash via the "update" function so that the file metadata is
    preserved.
    - The path to the trash folder is configured in settings.json > "files" > "trash"
    - The trash folder cannot be deleted from inside the application
    - When a file is moved to the trash, the alert is changed to a warning that says the
    file was moved to the trash folder
    - When importing migration files with "empty database" set to True, or running the mass
    deletion mechanism ("database deletion"), unix files are left untouched.
  - Detect missing files when running scan folder mechanism and mark them as "Not Found"
  - Drag-n-drop the same file multiple times in upload panel no longer possible
  - Use scoped path for playbooks in ansible service (impact on migration files)
- Fix log not sent when add_secret is False or device is None in the get_credentials function bug
- Add new 'prepend_filepath' function in workflow builder namespace to add path to file folder before a string
- Add support for string substitution for the email notification feature (service step 4)
- Limit update all pools mechanism (in pool table and as a service option) to the pools a user
  has "edit" access to

Migration:
- in file.yaml, remove path to "files" folder for all paths
- in service.yaml, compute and add new "read_timeout" property based on fast_cli,
  delay_factor and global_delay_factor
- in service.yaml, ansible playbook services are now used the scoped path to the playbook
  instead of the full path (path to playbook folder + scoped path). The path to the playbook
  folder must be trimmed from all ansible services.

Version 4.4.0: RBAC and Credentials
-----------------------------------

- Remove settings from UI upper menu (doesn't work with multiple gunicorn workers)
- Add post_update function (60350ede71f6a5146bab9f42a87f7fef0360b98e) after db flush in controller update function to compute pool only after the ID has been set, and
  determine what properties to return (e.g. not serialized object but only what is needed)
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
  fails (e.g. data too long db error because of payload data for the results),
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
- Fix bulk deletion and bulk removal from a filtered table (e.g. dashboard bulk deletion deletes everything,
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
  the database (e.g. first authentication method used)
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
- Make corrupted edges deletion mechanism a troubleshooting snippet instead of a button in the admin panel.
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
  ticked, meaning that each time a Unix Command service is edited, it must be re-approved.
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
  - Refresh rates in settings.json to be updated (e.g. 10s instead of 3 if RBAC is used)
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
- Add server time at the bottom of the menu (e.g. for scheduling tasks / ease of use)
- Add button in service table to export services in bulk (export all displayed services as .tgz)
- Ability to paste device list (comma or space separated) into a multiple instance field (e.g. service device and pool targets)
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
  for a netmiko validation command or rest call service. For obfuscation purposes.
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

  - "admin" (not part of RBAC, only admin have access, e.g. admin panel, migration etc)
  - "all" (not part of RBAC, everyone has access, e.g. dashboard, login, logout etc)
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
- Make the error page colors configurable per theme (move css colors to theme specific CSS file)
- Use the log level of the parameterized run instead of always using the service log level
- Change field syntax for context help to be 'help="path"' instead of using render_kw={"help": ...}
- Don't update the "creator" field when an existing object is edited
- Add new function "get_neighbors" to retrieve neighboring devices or links of a device
- Refactor the migration import mechanism to better handle class relationships
- Web / Desktop connection to a device is now restrictable to make the users provide their own credentials
  => e.g. to prevent inventory device credentials from being used to connect to devices
- Configuration git diff: indicate which is V1 and which is V2. Option to display more context lines, including all of it.
- Improve display of Json property in form (make them collapsed by default)
- Update to new version of Vis.Js (potential workflow builder impact)
- Add mechanism to save only failed results (e.g. for config collection workflow)
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
- Add placeholder as a global variable in a workflow (e.g. to be used in the superworkflow)
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
  no results (e.g. job still running), and the results if the job is done.
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
- Fix bug when typing invalid regex for table search (eg "(" ))
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
  service but also after the on-going device, or after the on-going retry (e.g. many retries...).
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
- Slashes are now forbidden from services and workflow names (conflict with Unix path)
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
