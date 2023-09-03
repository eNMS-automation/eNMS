# Customization 

## Custom Properties

The custom properties files in `setup/properties.json` allows for several types
of customization.

### Additional Properties  

The base objects in eNMS (Device, Link, Service, Workflow) can be extended with
"custom" properties to add additional properties.  In `properties.json` file,
these properties are stored under the `"custom"` key.

Custom properties accept these configuration elements:

- `pretty_name` (**optional**): Custom name of the property in the UI.
- `type` (**mandatory**): `string`, `integer`, `float`, `boolean`, `dict`,
  `json`, `select`, and `multiselect`.
- `default` (**optional**): Default value.
- `default_function` (**optional**): Function returning the default value. 
   This function **must** be an attribute of CustomApp in custom.py.
- `help` (**optional**): the path to a context-sensitive HTML help file for
   this property.
- `log_change` (**optional**): false - disables logging when a change is
   made to attribute.
- `private` (**optional**): If `true`, the value is considered sensitive: it 
   will not be displayed in the UI. It will be encrypted in the database and
   stored in the Vault (if the Vault has been set up).
- `is_address` (**optional**): `true` - this property can be used for
   connecting to network devices (e.g.,  hostnames, IP addresses, etc.).
- `configuration` (**optional**): `true` - creates a custom 
  `Inventory -> Configurations` attribute.
- `form` (**optional**): `false` - disables option to edit attribute in
   the User Interface.
- `migrate` (**optional**): `false` - choose if attribute should be considered
   for migration.
- `serialize` (**optional**): `false` - whether it is passed to the front-end
   when the object itself is.
- `merge_update` (**optional**): `false` - *only for JSON property* - whether
   the JSON value is overridden or updated when setting a new value from the
   REST API.
- `render_kw` (**optional**): dictionary which provides default keywords 
    to the WTForm widget at render time.

Example for a Device property:

```json
    "device": {
      "custom_multiselect": {
        "pretty_name": "Custom Multiselect",
        "log_change": false,
        "choices": [
          ["a", "A"],
          ["b", "B"],
          ["c", "C"]
        ],
        "default": ["a", "c"],
        "type": "multiselect"
      },
  }
```

Example for a Service property:

```json
    "service": {
      "impacting": {
        "pretty_name": "Impacting",
        "type": "bool",
        "default": true,
        "help": "custom/impacting"
      },
  }
```

Example of a default_function attribute:
```python
# eNMS/custom.py
from uuid import uuid4

class CustomApp
  def gererate_uuid(self):
    return str(uuid4())
```

```json
"service": {
   "uuid": {
     "pretty_name": "UUID",
     "type": "str",
     "default_function": "generate_uuid"
   }
}
```

      
!!! note

    Some *optional* values for custom properties above are *changes* to the
    default behavior. i.e "migrate" defaults to true, "private" defaults
    to false, etc.      

!!! tip

    Custom properties are defined ONCE, prior to eNMS starting up for
    the first time, since they are mapped into the database schema. Changes
    to customized properties require the database to be altered or dropped
    and reloaded to allow the object relational mapping to recreate the
    schema.

### Dashboard Configuration

The `"dashboard"` key in `properties.json` defines the model data (e.g.,
`"device"`) and properties to display in the eNMS Dashboard.

This data associated with this key allows determines how the [Dashboard](../system/dashboard.md):
1. chooses which object types (Devices, Links, etc.) to display, and  
2. applies a filter for each object type in each chart (`model`, `vendor`, etc.)

Example of a possible dashboard configuration:

```json
  "dashboard": {
    "device": ["model", "vendor", "subtype","operating_system"],
    "link": ["model", "vendor", "subtype", "location"],
    "service": ["vendor","operating_system","creator"],
    "workflow": ["vendor","operating_system","creator"],
    "task": ["status", "creator", "last_scheduled_by", "scheduling_mode"],
    "user": ["is_admin", "authentication", "groups"]
  },
```

### Table Columns

Column/field property visibility can be controlled in the device and link
inventory, configuration, and pools tables, as well as the service, results,
and task browsers.

The `"tables"` key in `properties.json` defines the properties displayed by the
eNMS tables for Devices, Links, etc. Any new, custom properties can also be
added here.

Example of this configuration data:  
  
- `"data": "device_status"`, *attribute created in custom device above*.
- `"title": "Device Status"`, *name to display in table*.
- `"search": "text"`, *search type*.
- `"width": "80%"`, *optional - text alignment, other example: "width":"130px",*.
- `"visible": false`, *default display option*.
- `"orderable": false`, *allow user to order by this attribute*.

### Table Filtering

The `"filtering"` key in `properties.json` defines the properties that can be
filtered in the tables for Devices, Links, etc. Any new, custom properties can
also be added here - if they should be used to filter the table.

- Values under `"filtering" : { "device" : [`
  Details which attributes to use for filtering. The user will need to add any
  custom device attributes name to this list for filtering.


## Custom Devices and Links

eNMS provides the ability to define specialized Device and Link classes.
The **Gateway** class (`eNMS/models/devices/gateway.py`) provides an example of this.

## Custom Libraries

The [Installation section](../../base/installation/#paths-section) describes
how to configure a directory from which to load custom Python modules (i.e.,
`"paths"` key in `settings.json`).  This allows Services and Workflows the
ability to import these modules.

## Custom Service Types

In addition to the service types provided by eNMS, custom Service
Types can be created. When the application starts, it loads all Python
files in the `eNMS/services` folder. Custom service types are then 
loaded from the folder specified in eNMS `settings.json`, section `paths`.

Creating a Service Type means adding a new Python file in that folder 
(creating sub-folders are fine to organize the custom services; they are
automatically detected). Just like all the service types, each
custom Service file must contain:

-   A **job()** function: that handles the action to be performed.
-   A **model** class: The service parameters, and what the service is
    doing via a `job` function.
-   A **form** class: The different fields eNMS displays in the UI, and
    their corresponding validation.
 
After adding a new custom Service type, the application must be reloaded,
which causes the resulting schema for the custom service type(s) to be mapped
into the database by the SQLAlchemy ORM. Then, the new custom Service type
will appear in the Service Type pull-down in the UI.

An example custom Service file exists in `eNMS/models/services/examples/example.py`

!!! tip

    Plugins can also define Custom Service Types.
     
     
## Plugins

A Plugin represents a more advanced form of customization - that can include new data 
models, user interface components, API and form endpoints, and Custom Service Types.  

Self-contained extensions to the eNMS platform represent good candidates for plugins.

At startup, eNMS loads any plugins it finds inside the `eNMS/plugins` folder. 

### Example Plugins 

Some example eNMS plugins can be found here:

- [An example eNMS plugin](https://github.com/eNMS-automation/template-plugin)  
- [A sample eNMS Command-Line Interface (CLI)](https://github.com/eNMS-automation/cli-plugin)
