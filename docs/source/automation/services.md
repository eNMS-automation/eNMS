# Services are Units of Work

Services provide the smallest unit of automation in eNMS. Each service
type provides unique functionality that is easily configured to perform
complex operations in the network. Examples: remote command execution,
REST API calls, Ansible playbook execution, and many more.

Services can be powerful on their own, (e.g. ping all devices in the
network and send a status email). They can also be combined within
workflows to automate complex operations such as device upgrades.

Each service type provides a form for configuring its unique
functionality. Common forms are available on every service for defining
device targets, iteration, retries, pre and post processing, result
validation, notifications, etc.

eNMS comes with a number of "built-in" service types based on network
automation frameworks such as `netmiko`, `napalm` and `ansible`, but
custom service types can be created. Each service type must return a python
dictionary as a result, and dictionaries are the primary means by which
services exchange data. See the `Builtin Service Types` section for
details on each of the different service types.

## Service Management Panel

All services are displayed in the Service Management Panel in 
`Automation / Services`, where new services can be created and edited,
duplicated, deleted, and existing services run.

![Service Management Panel](../_static/automation/services/services.png)

The Service Management Panel has a number of controls at the top for
Filtering and Bulk operations:

-  `Columns` Selector - Choose which columns to display in the table
-  `Display Services hierarchically` (using hyperlinks in the scope of
   the workflow that they are contained in) or Display All Services
-  `Refresh` the Table
-  `Advanced Search:` for complex filtering of the table
-  `Clear Search` criteria
-  `Copy the Selection` of currently displayed Services to the clipboard
-  `Back navigation and Forward navigation`: For drilling into nested
   workflows with subworkflows and back out.
-  `New` / Create Service with Service Type pull-down Selector: This opens
   the Service Editor Panel discussed below.
-  `Import Service(s)`: Opens a panel to allow drag and drop of service
   .tgz files (created using the Export service feature) from the user's
   browser. One or multiple services can be uploaded / imported in this way.
   
!!! note
    When importing a workflow .tgz file from another instance of eNMS, and
    that workflow already exists on this instance, first remove all of the
    services and edges from the existing (destination) workflow. Or, delete
    the existing workflow altogether.  This will prevent eNMS from merging
    the services and edges from the two workflows, which could result in an
    unintended workflow graph.

!!! note
    Do not attempt to import a workflow .tgz file from an instance of eNMS
    that is running a different eNMS version.  Contact your system administrator
    regarding any necessary conversion.

The following features operate on Bulk Services that are currently
filtered in the table display.
  
-  `Export Services`:  Exports the filtered list of services in the table to
   a .tgz file that is downloaded to the user's browser.  
-  `Bulk Edit`:  Makes the same config change to all currently filtered
   services in the table display.
-  `Export as CSV`: Export the current filtered list of services in the
   table display to a .csv file that downloads to the user's browser.
-  `Bulk Deletion`: Deletes all services that are currently filtered in the
   table display.

Below the top button bar are the Quick Filter controls for filtering the table.

Each Service listed in the table has its own button bar on the right that
includes:

-  `View Logs`: Opens the Logs Viewer
-  `View Results`: Opens the Results Viewer
-  `Edit Service`: Opens the Service Editor Panel with default parameters when
   creating a new service and with saved service parameters when editing an
   existing service.
-  `Duplicate Service`: Opens the Service Editor Panel with all parameters
   duplicated to the original service; create a new Service Name to complete.
-  `Export Service`: Downloads that Service to the browser in a .tgz file
   containing a YAML file representation of the service profile. 
-  `Run Service`: with the saved parameters inside the Service
-  `Parameterized Run`: Run the service after soliciting input fields from the
   user. Input field selection is controlled by the selection of parameters
   in the Step 1 Service Panel Editor.
-  `Delete Service`: Deletes this service. 

!!! Note

	Exporting services: In addition to the .tgz file that is downloaded to
    the browser, a copy of the .tgz file is stored in the `files/services`
    directory. This is intended for administrators migrating services from
    one instance of eNMS to another when deploying multiple instances.

## Service Editor Panel

The Service Editor Panel is accessible from the following locations:

![Service Editor Panel](../_static/automation/services/service_editor.png)

- `Automation -> Services` button bar for existing services 
- `Automation -> Workflow Builder` by double clicking an existing service
  or using the `Edit` button to edit a workflow (Workflows are services too).
  Also right mouse click on an existing Service, and then select `Edit`.
- `+` button in both `Automation -> Services` and `Workflow Builder` to create
  new Services from the Service Types pull-down.
  

### Section `Step 1: General`

![Service Editor Step1](../_static/automation/services/service_editor_step1.png)

#### Main Parameters

-   `Name`: (**mandatory**) Must be unique either within the
    enclosing workflow or unique among top-level services.
-   `Full Name`: (**display only**) Fully qualified service name including all
    workflow nesting or a **\[Shared\]** tag.
-   `Default Access`: Role Based (Creator) Allows access by the user that
    created the service and follows RBAC access using the Groups field.
    `Public` Allows access to anyone. `Admin` Limits access to admin users.
-   `Groups` Specifies which user groups have access to this service
-   `Owners` Further restricts service access to a list of owners
-   `Owners Access` Restrict what owners can do: Run and/or Edit the service.
-   `Service Type`: (**display only**) The service type of the current
    service instance.
-   `Shared`: Checked for **Shared** services. 

!!! Note

	Services can be standalone, shared, or scoped within a workflow. Shared
	services (or subworkflows) can exist inside multiple workflows, and a
	change to a shared service affects all workflows that use it. A service
	which is scoped within a workflow, either by creating the service inside
	the workflow or by deep copying the service into the workflow, exists
	only inside that workflow, so changes to it only affect its parent
	workflow. A standalone service exists outside of any workflow. A
	superworkflow acts as a template or wrapper around another workflow and
	allows for services to be run before and after the main workflow (which
	exists inside the superworkflow as a Placeholder). Because multiple
	workflows can specify the same superworkflow, the superworkflow acts as
	if it is shared.

- `Workflows`: (**display only**) Displays the list of workflows that
    reference the service.
- `Description` / `Vendor` / `Operating System`: Useful for filtering
    services in the table.
- `Initial Payload`: User-defined dictionary that can be used anywhere
    in the service.
- `Parameterized Form`: (default is configurable in `setup/automation.json`)
    A user defined input form 
    that pops up before a Parameterized Run of the service. Values entered 
    to this form at runtime are available within running services and can
    override properties of the "Run" class.  Forms defined on nested
    services or subworkflows are not displayed.
- `Parameterized Form is Mandatory`: Force display of the 
    Parameterized Form before execution whenever the service is run
    interactively.
- `Priority`: (default: `1`) Allows the user to determine the order a
    service runs when two services are ready to run at the same time.
    The service with a higher priority number is run first.
- `Number of retries`: (default: `0`) Number of retry attempts when the
    service fails. If the service has device targets, this is the number
    of retries for each device.
- `Time between retries (in seconds)`: (default: `10`) Number of
    seconds to wait between each attempt.
- `Maximum number of retries`: (default: `100`) Used to prevent infinite
    loops in workflows.  Users are able to manipulate the `retries`
    variable in `post processing` for service results.  Once this 
    number of retries is reached, the service will fail.
    
!!! Note

	The retry will affect only the devices for which the service failed.
	Let's consider a service configured to run on 3 devices D1, D2, and D3
	with 2 "retries". If it fails on D2 and D3 when the service runs for
	the first time, eNMS will run the service again for D2 and D3 at the
	first retry. If D2 succeeds and D3 fails, the second and last retry will
	run on D3 only.    
    
- `Type of Credentials`: (default: Any) Allows the user to limit the type
    of credential used when running the 
    service to Read versus Read-Write credentials, assuming both credentials
    are accessible by the user. 
- `Logging`: (default: `Info`, configurable in `setup/logging.json`) 
    The log level to use when running the service; it governs logs written
    to the log window in the UI, as well as the logs that are written to
    the log files.
- `Save only failed results`: (default: False) If enabled, the service
    will not generate a result unless there was a failure. This saves
    database space and improves performance. Beware if a subsequent service
    needs to rely on this service's result.
- `Update pools after running`: (default: False) Update all pools after
    this service runs. Note that updating all pools is performance intensive.

#### Workflow Parameters

This section contains the parameters that apply **when the service runs
inside a workflow only**.

-   `Preprocessing`: A python script that
    runs before the service is executed. If the service has device
    targets, the code will be executed for each device independently,
    and a `device` global variable is available. Preprocessing is
    executed for standalone services and those within a workflow. This
    feature is useful for setting initial condition variables using
    `set_var()` that can be used for conditional processing within the
    service or workflow elsewhere; for example using the same workflow
    to perform pre- and post- check tests on a device.
-   `Skip Query`: This field expects a python expression that evaluates
    to either `True` or `False`. The service will be skipped if `True`
    and will run otherwise.
-   `Skip Value`: Defines the success value of the service when skipped
    (in a workflow, the success value defines whether to follow the
    success path (success edge), the failure path (failure edge), or be
    discarded (in which case no result is created and the workflow graph
    will not proceed for that device). Note that another parallel part of
    the workflow might still generate a result for the device if discarded
    in one path (when parallel paths are used in the workflow).
-   `Maximum number of runs`: (default: `1`) Number of times a service is
    allowed to run in a workflow
-   `Time to Wait before next service is started (in seconds)`: (default:
    `0`) Number of seconds to wait after the service is done running.

#### Custom Properties

The eNMS administrator can add extra properties to the service form that
are saved on the service instance.  These Custom Property definitions are added
in `setup/properties.json`.  A field for entry of Custom Property values is
included in the Custom Properties section.

Additional information for these fields
may be available using the help icon next to the field label.

The location for the help files can specified in the `setup/properties.json`,
for example:

		"help": "custom/impacting"

### Section `Step 2: Specific`

This section contains all parameters that are specific to the service
type. For instance, the "Netmiko Configuration" service that uses
Netmiko to push a configuration will display Netmiko parameters (delay
factor, timeout, etc) and a field to enter the configuration to push to
the device.

![Service Editor Step2](../_static/automation/services/service_editor_step2.png)

The content of this section is described for each service in the
`Built-in Services` section of the docs.

### Section `Step 3: Targets`

![Service Editor Step3](../_static/automation/services/service_editor_step3.png)

#### Devices
`Run method` on a workflow: Defines whether the workflow runs a device at a
time or a service at a time, and whether device targets are taken from the
workflow or each service.

`Run Method` on a service: Defines whether the service should run exactly once,
or if it should run once per device. Most built-in services are designed to
run once per device.

The run method, targets, and multiprocessing defined on a workflow and nested
services work together in a complex way.  The table below describes each combination:

<table>
<thead>
  <tr>
    <th>Enclosing Workflow<br> Run Method</th>
    <th>Child Service<br>Run Method</th>
    <th>Behavior</th>
  </tr>
</thead>
<tbody>
  <!-- Standalone Service -->
  <tr>
    <td rowspan="2">Standalone Service<br>(No enclosing workflow)</td>
      <td>Run the service once per device</td>
      <td>The service runs once for each device.<br>  Devices come from the service.<br>  Multiprocessing allows multiple instances of the service to run concurrently, each for a different device. </td>
  </tr>
  <tr>
      <td>Run the service once</td>
      <td>The service runs exactly once.<br> Devices come from the service.<br> Multiprocessing has no effect.</td>
  </tr>

  <!-- Device by Device -->
  <tr>
    <td rowspan="2">Run the workflow device by device</td>
      <td>Run the service once per device</td>
      <td>Each device flows through the workflow independently.<br> Run Method on nested services is irrelevant because the workflow is run for a single device at a time.<br>Devices come from the workflow.<br> Multiprocessing on the workflow allows multiple devices to run the entire workflow concurrently and is ignored on nested services.</td>
  </tr>
  <tr>
      <td>Run the service once</td>
      <td>This combination is misleading because each device runs the workflow independently.<br> Do not use this combination of Run Methods.</td>
  </tr>

  <!-- Service by Service with Workflow Targets -->
  <tr>
    <td rowspan="2">Run the workflow service by service using workflow targets</td>
      <td>Run the service once per device</td>
      <td>Each service runs for all devices before moving to the next service.<br>  Devices come from the workflow and are ignored on the service.<br>  Multiprocessing on the service allows multiple devices to run the service concurrently.  Multiprocessing on the workflow is ignored.</td>
  </tr>
  <tr>
      <td>Run the service once</td>
      <td>The service runs exactly once.<br> Devices come from the workflow and are ignored on the service.<br> Multiprocessing on the workflow or service has no effect as the service runs once.</td>
  </tr>

  <!-- Service by Service with Service Targets -->
  <tr>
    <td rowspan="2">Run the workflow service by service using service targets</td>
      <td>Run the service once per device</td>
      <td>Each service runs for all devices before moving to the next service.<br>  Devices come from the service and are ignored on the workflow.<br>  Multiprocessing on the service allows multiple devices to run the service concurrently.  Multiprocessing on the workflow is ignored.</td>
  </tr>
  <tr>
      <td>Run the service once</td>
      <td>The service runs exactly once.<br> Devices come from the service and are ignored on the workflow.<br> Multiprocessing on the workflow or service has no effect as the service runs once.</td>
  </tr>
  
</tbody>

</table>

The python variables `device` and `devices` provide access to the current device
and the full set of devices.  No concept of a current device exists for services
with run method `Run the service once`; therefore the `device` variable may be
`None`.

#### Iteration

Multiple actions are sometimes necessary when the service is triggered
for a target device. Use iteration devices when those actions should be
performed on a set of devices related to the current target device. Use
iteration values when the actions should be performed on the current
target device.

-   `Iteration Devices`: Query that returns an **iterable** (e.g. Python
    list) of **strings (either IP addresses or names)**.
    -   The service is run for each device as the target device,
        allowing operations against a set of devices related to the
        original target.
    -   `Iteration Devices Property` Indicates whether iterable
        `Iteration Devices` contains IP addresses or names, for eNMS to
        look up actual devices from the inventory.
-   `Iteration Values`: Query that returns an **iterable** (e.g. Python
    list) of **strings**.
    -   The service is run for each value.
    -   `Iteration Variable Name` Python variable name to contain each
        successive value from the `Iteration Values` query. The resulting
        `Iteration Variable` is a global variable and can be accessed anywhere
        in the workflow directly to get the list of values without needing
        get_var().

`Iteration Devices` and `Iteration Values` can be used together.  Conceptually,
this is like three levels of nested loops where the service is run for each
combination of target device, iteration device, and iteration value.

### Section `Step 4: Result`

![Service Editor Step4](../_static/automation/services/service_editor_step4.png)

The `Result` section defines operations on the service result. Each form
group offers a different type of results operation. These operations are
performed **in the order found on the `Result` page**. Result operations are
executed for each device for `Run method` **Run the service once per device**,
and are executed only once for `Run method` **Run the service once**.

#### Conversion and Postprocessing

-   `Conversion Method`: The type of automatic conversion to perform on
    the service result.
    -   `No conversion`: (default) Use the result with no modification.
    -   `Text`: Convert the result to a python string.
    -   `JSON`: Convert a string representing JSON data to a python
        dictionary.
    -   `XML`: Convert a string representing XML data to a python
        dictionary.

Python can be used to inspect or modify the service result. This is
typically used to perform complex validation or to extract values from
the result for use in subsequent services.

-   `Postprocessing Mode`: Control whether or not the `Postprocessing`
    script is executed
    -   `Always run`: The `Postprocessing` script will
        execute for each device
    -   `Run on success only` (**default**) 
    -   `Run on failure only`
-   `PostProcessing`: A python script to inspect or update the current
    result.
    -   Variable **results**
        -   Contains the full results dictionary for the current device,
            exactly as seen in the results view.
            -   Changes to this dictionary are reflected in the final
                result of the service.
        -   **results["success"]** The overall service status.
        -   **results["result"]** The resulting data from running
            the service.
    -   See [Using python code in the Service Editor Panel](#using-python-code-in-the-service-editor-panel) for the full
        list of variables and functions.
    -   Note that a log is generated any time postprocessing is skipped

#### Validation

Validation can consist of:

**Text matching**: looking for a string in the result, or matching
the result against a regular expression.

**Dictionary matching**: Check that a dictionary is included or
equal to the result.

**Anything else**: The user can use python code to change the result,
including the value of the `success` key.


- `Validation Condition`: When to run Validation on the result:
    -   `No validation`: No validation is performed
    -   `Run on success only`
    -   `Run on failure only`
    -   `Always run`
- `Validation Method`: The validation method depends on whether the
    result is a string or a dictionary.
    -   `Validation by text match`: Matches the result against `Content Match`
        (string inclusion, or regular expression if
        `Match content against Regular expression` is selected)
    -   `Validation by dictionary inclusion`: Check that all `key` : `value`
        pairs from the dictionary provided in `Dictionary Match` can be found
        in the result.
    -   `Validation by dictionary equality`: Check for equality against the
        dictionary provided in `Dictionary to Match Against`
- `Section to Validate` : (default: `results['result']`) Which part of the
    payload dictionary to perform validation on
- `Content Match` : Text to Match against when `Validation by text match`
    is selected above.
- `Content Match is a regular expression`: Instructs eNMS to treat the
    match text as a regular expression for `Validation by text match`.
- `Dictionary to Match Against`: Provide a dictionary in `{}` for performing
    dictionary inclusion and equality matches.
- `Delete spaces before matching`: (`Text` match only) All whitespace
    is stripped from both the output and `Content Match` before
    comparison to prevent these differences from causing the match to
    fail.
- `Negative Logic`: Reverses the `success` boolean value in the
    results: a success becomes a failure and
    vice-versa. This provides a simpler solution than using negative
    look-ahead regular expressions.

#### Notifications

When a service finishes, the user can choose to receive a notification with
the results. There are three types of notifications:

**Mail notification**: eNMS sends an email to provided address(es)

**Slack notification**: eNMS sends a message to a provided Slack channel

**Mattermost notification**: eNMS sends a message to a provided Mattermost
channel

Configure the following parameters:

-   `Send Notification`: Enable sending results notification
-   `Notification Method`: Mail, Slack or Mattermost.
-   `Notification Header`: A header displayed at the beginning of the
    notification.
-   `Include Device Results`: for service (not workflow) level notifications
-   `Include Result Link in summary`: Whether the notification contains
    a link to the results.
-   `Mail Recipients`: Must be a list of email addresses, separated by
    comma.
-   `Reply-to Email Address`: Must be a list of email addresses, separated by
    comma.
-   `Display only failed nodes`: The notification will not include
    devices for which the service ran successfully.

To set up the mail system, the parameters in the `mail`
section of the settings must be configured: `server`, `port`, `use_tls`,
`username`, `sender`, `recipients`, and the password must be set via the
`MAIL_PASSWORD` environment variable.

The `Mail Recipients` parameter must be set for the mail system to work;
the `Admin > Administration` panel parameter can also be
overridden from Step 2 of the Service Instance and Workflow configuration
panels. For Mail notification, there is also an option in the Service
Instance configuration to display only failed objects in the email
summary versus seeing a list of all passed and failed objects.

In Mattermost, if the `Mattermost Channel` is not set, the default
`Town Square` will be used.

## Using python code in the Service Editor Panel

There are two types of fields in the service panel where the user is
allowed to use pure python code: substitution fields (light blue
background) and python fields (light red background). In these fields,
the user can use any python code, including a number of **variables** that
are made available to the user.

### Variables

- `delete()`
    -   **Meaning**: Allows for deleting one of the following object types
        in the database: `device`, `link`, `pool`, `service`. Calling
        this from a workflow requires the user to have edit access to the
        object type; otherwise it will fail.
        **Type**: Function.
        **Available**: Always.
    -   **Return Type**: Object that was created or None
    -   **Parameters**:
        -   `model`: (**mandatory string**) `device`, `link`, `pool`, or `service`

- `device`
    -   **Meaning**: This is the current device on which the service is
        running. `device` is not defined in contexts without a concept
        of a current device.
    -   **Type**: Database Object.
    -   **Available**: When the service is running on a device.
    -   **Properties**: Member attributes which can be referenced as
        `{{device.property}}`, such as `{{device.name}}` or
        `{{device.ip_address}}`, inside of forms. The following base
        properties are supported:

        - device.name
        - device.subtype
        - device.description
        - device.model
        - device.location
        - device.vendor
        - device.operating_system
        - device.os_version
        - device.ip_address
        - device.latitude
        - device.longitude
        - device.port
        - device.configuration
        - device.last_failure (last failure timestamp fo
          configuration collection)
        - device.last_status (last status timestamp for configuration
          collection)
        - device.last_update (last update timestamp for configuration
          collection)
        - device.last_runtime (last runtime timestamp fo
          configuration collection)
        - device.last_duration (last time duration for configuration
          collection)
        - [Custom device properties, if implemented](custom_device_properties.md)

- `devices`
    - **Meaning**: The set of target devices for the service or workflow,
        i.e., the union of devices, pools, and the device query. Device by
        device workflows run one device at a time therefore `devices`
        contains only one device, not the full list.
    - **Type**: Set of Database Objects.
    - **Available**: In service by service workflows.

- `factory()`
    -   **Meaning**: Allows for creating one of the following object types
        in the database: `device`, `link`, `pool`, `service`. Calling
        this from a workflow requires the user to have edit access to the
        object type; otherwise it will fail.
        **Type**: Function.
        **Available**: Always.
    -   **Return Type**: Object that was created or None
    -   **Parameters**:
        - `model`: (**mandatory**) `device`, `link`, `pool`, or `service`
        - `commit`: (**optional**) `True` or `False`(Default)
        - Model properties: Specify values for the new instance: 
          ip_address="1.2.3.4" when creating a new device. 
           
- `fetch()`
    -   **Meaning**: Allows for retrieving one of the following object types
        from the database: `device`, `link`, `pool`, `service`. Calling
        this from a workflow requires the user to have edit access to the
        object; otherwise it will fail.
        **Type**: Function.
        **Available**: Always.
    -   **Return Type**: Database Object or List of Database Objects
    -   **Parameters**:
        - `model`: (**mandatory**) `device`, `link`, `pool`, or `service`
        - `allow_none`: (**optional**) `True` or `False`(Default)
        - `allow_matches`: (**optional**) `True` or `False`(Default)
        - Model propertes: (**mandatory**) Property values to identify
          the desired object: ip_address="1.2.3.4".
  
- `fetch_all()`
    -   **Meaning**: Allows for retrieving all instances for one of the
        following object types from the database: `device`, `link`, `pool`,
        `service`. Calling this from a workflow requires the user to have
        edit access to the object; otherwise it will fail.
        **Type**: Function.
        **Available**: Always.
    -   **Return Type**: Database Object or List of Database Objects
    -   **Parameters**:
        - `model`: (**mandatory**) `device`, `link`, `pool`, or `service`
        - `allow_none`: (**optional**) `True`(Default) or `False`
        - `allow_matches`: (**optional**) `True`(Default) or `False`
        - Model properties: (**optional**) Filter values to limit the set of
          returned objects: vendor="Cisco".
            
- `get_neighbors()`
    -   **Meaning**: Used to return links or devices connected to the target
        device
    -   **Type**: Function.
    -   **Available**: When the service is running on a device, this function
        must be called on a `device` object
    -   **Parameters**:
        -   `object`: (**mandatory**) `device` or `link`
        -   `direction`: (**optional**) `source` or `destination`
        And optionally, any number of the Link **properties** can be passed as
        parameters as well. The following base properties are supported:
        -   `name`
        -   `description`
        -   `subtype`
        -   `model`
        -   `source_name` (source device name)
        -   `destination_name` (destination device name)
        -   [Custom link properties, if implemented](custom_link_properties.md)
        
- `get_result()`
    -   **Meaning**: Fetch the result of a service in the workflow that
        has already been executed.
    -   **Type**: Function.
    -   **Return Type**: Dictionary
    -   **Available**: When the service runs inside a workflow.
    -   **Parameters**:
        -   `service`: (**mandatory**) Name of the service
        -   `device`: (**optional**) Name of the device, when you want to
            get the result of the service for a specific device.
        -   `workflow`: (**optional**) If the workflow has multiple
            subworkflows, a subworkflow can be specified to get the
            result of the service for a specific subworkflow.

- `get_var()`
    -   **Meaning**: Retrieve a value by `name` that was previously
        saved in the workflow. Use `set_var()` to save values. Always use
        the same `device` and/or `section` values with `get_var()` that
        were used with the original `set_var()`.
    -   **Type**: Function.
    -   **Return Type**: None
    -   **Available**: Always.
    -   **Parameters**:
        -   `name`: Name of the variable
        -   `device`: (**optional**) The value is stored for a specific
            device.
        -   `section`: (**optional**) The value is stored in a specific
            "section".

- `log()`
    -   **Meaning**: Write an entry to a log file
    -   **Type**: Function
    -   **Return Type**: None
    -   **Available**: Always.
    -   **Parameters**:
        -   **severity**: (**string**) Valid values in escalating
            priority order: **debug**, **info**, **warning**, **error**,
            **critical**.
        -   **message**: (**string**) Verbiage to be logged.
        -   **device**: (**string**, **optional**) Associate log message
            to a specific device.
        -   **app_log**: (**boolean**, **optional**) Write log message
            to application log in addition to custom logger.
        -   **logger**: (**string**, **optional**) When specified, the
            log message is written to the named custom logger instead of
            the application log. Set **app_log** = True to send log
            message to both the custom and application logs. Loggers are
            defined in the `setup/logging.json` configuration file.

- `parent_device`
    -   **Meaning**: Parent device used to compute derived devices.
        `parent_device` is useful when using iteration devices where
        `device` is the current iterated device and `parent_device` is
        the current device from (service or workflow) targets. When not
        using device iteration, `device` and `parent_device` are equal.
    -   **Type**: Database Object.
    -   **Available**: When the iteration mechanism is used to compute
        derived devices.

- `payload`
    -   **Meaning**: This is the entire dictionary of variables defined by
        `set_var()` and populating the `initial_payload` field for a workflow.
    -   **Type**: Dictionary.
    -   **Available**: Always.
    
- `placeholder`
    -   **Meaning**: This is the reference inside a superworkflow for the main
        workflow that the superworkflow wraps around. A superworkflow must have
        the `placeholder` service added to its graph in order to function.
    -   **Type**: Database Object of type Service.
    -   **Available**: When a service is running inside a superworkflow.

- `results`
    -   **Meaning**: The results of the current service.
    -   **Type**: Dictionary.
    -   **Available**: After a service has run.
        
- `set_var()`
    -   **Meaning**: Save a value by `name` for use later in a workflow.
        When `device` and/or `section` is specified, a unique value is
        stored for each combination of device and section. Use `get_var`
        for value retrieval.
    -   **Type**: Function.
    -   **Return Type**: None
    -   **Available**: Always.
    -   **Parameters**:
        -   `name`: Name of the variable
        -   `device`: (**optional**) The value is stored for a specific
            device.
        -   `section`: (**optional**) The value is stored in a specific
            "section".

!!! note

    Variables saved globally (i.e. set_var("var1", value) and for a device
    (i.e. set_var("var2", device=device.name)) are made available as global
    python variables within
    every Python code-field within the forms. This allows users to reference
    values as `var1` and `var2` in subsequent services.  get_var is required
    for access
    to values set for a device other than the current device and for those
    using a section scope. 
    
!!! note
  
    If both a global and device specific set_var variable is defined with the
    same name, only the device specific is made available as a global Python
    variable.  Use get_var() to access the same name set at a different scope.

!!! warning

    The payload (including all set_var variables) is rendered as JSON and saved
    in the database as part of the result.  JSON does not support recursive
    data structures, i.e. data structures with loops.  Saving a reference
    within the payload (or set_var variable) to a value from a higher level
    in the payload will result in a `Recursion Error`.  For example,
    `payload['mydict']['another_dict'] = payload` or
    `set_var("my_payload", payload)` each result in a loop from within the
    payload to a higher level in the payload. 

-   `settings`

    -   **Meaning**: eNMS settings, editable from the top-level `Settings`
        Icon. It is initially set to the content of `settings.json`, and
        it stays synchronized if the option to write changes back to 
        `settings.json` is used.
    -   **Type**: Dictionary.
    -   **Available**: Always.

-   `send_email` allows for sending an email with optional attached file. It
    takes the following parameters:

    -   `title`: (**string, mandatory**)
    -   `content`: (**string, mandatory**)
    -   `sender`: (**string, optional**) Email address of the sender.
        Defaults to the sender address in eNMS settings.
    -   `recipients`: (**string, optional**) Mail addresses of the
        recipients, separated by comma. Defaults to the recipients'
        addresses in eNMS settings.
    -   `reply_to`: (**string, optional**) Single mail address for
        replies to notifications
    -   `filename`: (**string, optional**) Name of the attached file.
    -   `file_content`: (**string, optional**) Content of the attached
        file.

    ``` 
    send_email(
        title,
        content,
        sender=sender,
        recipients=recipients,
        reply_to=reply_to,
        filename=filename,
        file_content=file_content
    )
    ```

-   `dict_to_string` - convert a dictionary to a string form with
    indentation. It takes the following parameter:

    -   `input`: (**`dict` or `any`, mandatory**)

    ``` 
    # Variable substitution example
    {{dict_to_string(get_var("the_variable_name"))}}
    ```

    ``` 
    # General example
    test = {'key': 'value', 'key2': [45, 1135, 544]}
    print(dict_to_string(test))
    # output:
    key: value
    key2:
            - 45
            - 1135
            - 544
    ```
    
-   `workflow`

    -   **Meaning**: current workflow.
    -   **Type**: Database Object.
    -   **Available**: when the service runs inside a workflow.

### Substitution fields

Substitution fields, marked in the interface with a light blue
background, lets the user include python code inside double curved brackets
(`{{user python code}}`). For example, the URL of a REST call service is
a substitution field. If the service is running on device targets, use 
the global variable `device` in the URL. When the service is
running, eNMS will evaluate the python code in brackets and replace it
with its value. See [Using python code in the service panel](#using-python-code-in-the-service-editor-panel)
for the full list of variables and functions available within substitution
fields.

![Variable substitution](../_static/automation/services/variable_substitution.png)

Running the service on two devices `Device1` and `Device2`, for example, will
result in sending the following GET requests:

``` 
"GET /rest/get/device/Device1 HTTP/1.1" 302 219
"GET /rest/get/device/Device2 HTTP/1.1" 302 219
```

### Python fields

Python fields, marked with a light red background, accept valid python
code (without the double curved brackets '{{}}' of the above Substitution
fields). Some examples of where Python fields are used:

-   In the `Device Query` field of the "Devices" section of a service.
    An expression that evaluates to an iterable containing the name(s)
    or IP address(es) of the desired inventory devices.
-   In the `Skip Query` field of the "Workflow" section of a
    service. The expression result is treated as a boolean.
-   In the `Python Exraction Query` field of the `Data Extraction Service`.
    The expression result is used as the extracted value.
-   In the code of a Python Snippet Service, or the `Preprocessing` and
    `Postprocessing` field of every service.

## Custom Service Types

In addition to the built-in service types provided by eNMS, custom service
types can be created. When the application starts, it loads all python
files in the `eNMS/services` folder. Custom service types are then 
loaded from the folder specified in eNMS `settings.json`, section `paths`.

Creating a service type means adding a new python file in that folder 
(creating sub-folders are fine to organize the custom services; they are
automatically detected). Just like all the built-in service types, each
custom service python file must contain:

-   A **job()** function: that handles the action to be performed
-   A **model** class: The service parameters, and what the service is
    doing via a `job` function.
-   A **form** class: The different fields eNMS displays in the UI, and
    their corresponding validation.
 
After adding a new custom service type, the application must be reloaded,
which causes the resulting schema for the custom service type(s) to be mapped
into the database by the SQLAlchemy ORM. Then, the new custom service type
will appear in the service types pull-down in the UI.

An example custom service file exists in `eNMS/services/examples/example.py`

## Running a Service

Services can be run from the following locations:

- `Automation->Services` table `Run` button beside each service
- `Automation->Workflow Builder` button bar to `Run` or `Parameterized Run` 
  the entire workflow, or right mouse click menu `Run` or `Parameterized Run`.
- `Automation->Scheduling`: Activated services will run when their scheduled
  time arrives.
- `Visualization` Maps:  A service can be selected to run on the filtered
  view/list of devices and links shown on the display.
- `Inventory` Devices, Links and Pools Tables: A service can be selected to run
  on the filtered list of devices and links in the table.   

There are two types of runs:

- Regular run: Uses the saved properties inside the service during the run.
- Parameterized run: A window is displayed with select properties to be 
  provided by the user without saving those properties inside the service.
  Properties selected for display in the parameterized run form are controlled
  in the `Step 1: Main Parameters` section of the `Service Editor Panel` 

## Inspecting Results

A separate result is stored for each run of a workflow, plus a
unique result for every device and for every service and
subworkflow / superworkflow within that workflow. Each result is displayed
as a JSON object dictionary. In the event that retries are configured, the
results dictionary will contain an overall results section, as well as a
section for each attempt, where failed and retried devices are shown in
subsequent sections starting with attempt2.

Results can be viewed in the following locations:

- `Automation->Results`: Shows the list of all results for the current user
- `Automation->Services`: See the `Results` button on the button bar
- `Automation->Workflow Builder`:

    - See the `Results` button on the button bar. 
    - The right mouse click menu has a `Results` option for the entire workflow
      or for a particular service depending on click location.
    - The `Result Tree` button opens a tree viewer panel of service results,
      each with a `Results` button, as well as an `All Results` button that 
      opens the results view table for all runtime results.
    - The `Result Comparison` button opens a filterable list of service
      and device results, which can be selected for comparison.
     
- Remote viewing: the `setup/logging.json` configuration can be modified to
  include a remote syslog endpoint for sending service results using the `log`
  function above. This option allows results to be integrated with a 
  time-series database and dashboard reporting software.

!!! note
    
    Results can be disabled, except for failures, with the `Save only failed
    results` option in `Step 1 Main Parameters` of the Service Editor Panel.
    This allows service and workflow data to be reduced and thus saves database
    space, but beware if subsequent services need to rely on these results.
    
!!! note
    
    When viewing the table of service and device results, a button exists to
    copy the get_result() path to the clipboard. This makes it convenient to
    paste the get_result() path into a variable substitution or python field
    elsewhere in the application to retrieve that result.
    
!!! note

    When viewing an individual result, a download button exists to download
    a json file with the result content to the user's browser.
  
## Inspecting Logs

Viewing device and service Logs is available at all of the above 
same results locations. The Log Viewer automatically pops up when a service
or workflow is manually initiated via the Services Management table or via
Workflow Builder, and the log window automatically scroll as logs occur.
Logs for scheduled tasks or REST API initiated automation
jobs produce logs, they but do not cause the Log Viewer panel to open.

The Log Viewer allows for the selection of a historical runtime to view logs
for, and the panel has a `Download Logs` button to download the text logs to
the user's browser.
