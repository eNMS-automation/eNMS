
## Transfer of Data between Services

### Using the Result of a Previous Service: `get_result()`

During a service's execution, the user can have access to the results of
all services in the workflow that have already been executed with a special
function called `get_result()`. The result of a service is the
dictionary that is returned by the `job()` function of the service, and
calling `get_result()` will return that dictionary. There are two types of
results: top-level and per-device. If a service runs on 5 devices, 6
results will be created: one for each device and one top-level result
for the service itself. The top-level results contain the parameters that
the service used during execution.

Examples:

- `get_result("get_facts")`: Get the top-level result for the service
  `get_facts`.
- `get_result("get_interfaces", device="Austin")`: Get the result of
  the device `Austin` for the `get_interfaces` service.
- `get_result("get_interfaces", device=device.name)`: Get the result of
  the current device for the `get_interfaces` service.
- `get_result("Payload editor")["runtime"]`: Get the `runtime` key of
  the top-level result of the `Payload editor` service.
- `get_result("get_interfaces", device=device.name, runtime="2024-07-15 05:18:35.48611572025")`:
  Get the result for the current device for the `get_interfaces` service, for the runtime
  `2024-07-15 05:18:35.48611572025`. By default, when no runtime is specified, the results for
  the current runtime are retrieved.

The `get_result()` function works everywhere that python code is accepted.

### Saving and Retrieving Values in a Workflow: `get_var(),set_var()`

The user can define variables in the payload with the `set_var()` function,
and retrieve those variables' data from the payload with the `get_var()`
function using the first positional argument (the variable name) and the
same optional arguments defined in `set_var`. If neither of the optional
arguments are used, the variable is global.

- The first argument for set_var is positional and names the variable
  being set.
- The second argument for set_var is positional and assigns the value
  for the variable.
- An optional argument for set_var uses keyword "device", which can
  scope the variable to the device the service is using when the
  variable is set.
- An optional argument for set_var uses keyword "section", which can
  scope the variable to a user provided custom scope.

Examples:

    set_var("global_variable", value=1050)
    get_var("global_variable")
    set_var("variable", "variable_in_variables", section="variables")
    get_var("variable", section="variables")
    set_var("variable1", 999, device=device.name)
    get_var("variable1", device=device.name)
    set_var("variable2", "1000", device=device.name, section="variables")
    get_var("variable2", device=device.name, section="variables")
    set_var("iteration_simple", "192.168.105.5", section="pools")
    get_var("iteration_simple", section="pools")
    set_var("iteration_device", devices, section="pools", device=device.name)
    get_var("iteration_device", section="pools", device=device.name)

### Update an object property: `try_set`

`try_set` can be called to update an object's property and commit it to the database. If the commit fails for any reason (database unavailable, deadlock, etc.), `try_set` will automatically roll back and attempt to commit again. The number of retries is configured in database.json.

- The first argument of try_set is the SQLAlchemy object to update.
- The second argument is the name of the property to update (as a string).
- The third argument is the value of that property.

### Commit a transaction: `try_commit`

`try_commit` can be called to run a function and attempt to commit the transaction at the end. If the commit fails for any reason (database unavailable, deadlock, etc.), `try_commit` will automatically roll back and attempt to commit again. The number of retries is configured in database.json.

- The first argument of try_commit is the function to run (the SQL transaction)
- The following arguments, *args and **kwargs, are passed to the function

Typical usage: `try_commit(transaction, *args, **kwargs)`

### Retrieving Links and neighboring Devices: `get_neighbors()`

The user can retrieve the list of links to and from the target device
as well as the neighboring devices at the ends of those links with the
`device.get_neighbors()` function. The function requires a mandatory
parameter `device` or `link` and optional parameters for the 
`direction=source` or `direction=destination` as well as any of the parameters
of the Link object.

Examples:

- `device.get_neighbors("device")`.
- `device.get_neighbors("link")`.
- `device.get_neighbors("device", direction="source"))`.
- `device.get_neighbors("link", direction="source"))`.
- `device.get_neighbors("device", direction="destination"))`.
- `device.get_neighbors("link", direction="destination"))`.
- `device.get_neighbors("device", model="10G"))`.
- `device.get_neighbors("link", model="400G"))`.
- `device.get_neighbors("device", direction="source", model="40G"))`.
- `device.get_neighbors("link", direction="destination", model="10G"))`.

The `device.get_neighbors()` function works everywhere that the target device
is defined and is dependent on the run method selected (see `Run Method` above
and in the Services section).

### Retrieve a Credential from the Vault: `get_credential()`

A user with `Admin` level access can call the `get_credential()` function
within a service to retrieve a credential object from the Vault. It returns
a dictionary with clear-text username and password. 

Example:
    get_credential(name="credential_name")
    
A use case would be to use "Unix Command" service to invoke a command that
requires the credential.  Logging should be deactivated for such a service
as the clear-text credentials would otherwise appear in the logs. A "Python
Snippet" service could accomplish the same task by using subprocess to run
the command on the server.

!!! note

    Make sure not to store the output of `get_credential()` in the result or in
    the payload (using one of the previously mentioned functions); otherwise,
    those values will be stored in the database.  They can be stored in the 
    payload temporarily as long as it is removed at the end of the workflow.