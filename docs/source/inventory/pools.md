# Pools

A Pool is a collection of objects of the following types:

- Devices
- Links
- Users
- Services

Pools can contain a single type of object or a mix of objects types.  For each
object type, a set of selection properties is used to determine which objects
of that type will be included in the pool. If the properties of a object
matches the pool properties, that object will be automatically included in
the pool. Alternatively, pools can be edited to manually select instead of
using criteria based on properties.

The context where a pool is used determines which object types are used from
a pool. For example, when a pool specifies the targets for a workflow, the
devices are used and links, users, and services in the pool are ignored.

Pools are used in several parts of the application:

- Targets of a Service or Workflow:  Device and/or Links can be added to a
pool, which is then selected as the execution target for a Service or Workflow
automation to run on.

    - Pools can also be specified as the execution targets of a Scheduled Task.
    If a pool is also specified as the target within the service or workflow,
    the Scheduled Task's pool will override which device and links the
    automation is executed against.
    
- Visualization Scope:  For both the Geographical and Logical Visualization 
panels, a pool is used to filter which objects are presented on the map. For
    - Geographical Visualization, the pool list only shows pools with devices
    and links. Pools of only Users and Services are omitted since these don't
    make sense to show on a map.
    - Logical Visualization, the pool list only shows pools with at least 1
    device and 1 link because the force-directed graph algorithm shows the
    interconnected relationships of the objects.
    
- RBAC (Role Based Access Controls): Pools are used in the 
  `Administration -> Access` menu to define which objects a user can access:
  Devices, Links, Services.  
    - Also, when defining credentials in `Administration -> Credentials',
    Pools of Users can be selected to define who can access that credential.

## Pool Management

![Pool Management](../_static/inventory/pools/pool_table.png)

The `Inventory -> Pools` menu supports the following operations on each pool
listed in the Pools table:

- Update:  perform a recalculation between pool properties and object
  properties to determine which objects match and will be included in the pool
  
- Edit: modify the properties for matching this pool

- Duplicate: copy this pool's properties to a new pool and make some
  slight modification for different criteria

- Run Service: run a service or workflow against this pool's device and links
  as the target of execution.
  
- Delete: delete this pool

From the menu bar above the table, the following operations are supported 
against all pools currently in the table.  Note that the table can be filtered
to reduce which pools are listed in the table, and for which of the menu bar
operations will be applicable:

- Refresh: refresh the table

- Advanced Search:  apply an advanced filter against the table to select which
  pools are listed.

- Clear Search: clear all filtering that has been applied to the table.
 
- Copy Selection to the Clipboard: Copy the list of Pools to the clipboard as
  a comma-separated list.
  
- New: Create a new Pool of objects

- Export:  Export the list of Pools as a .csv file that is downloaded to the 
  user's browser.
 
- Update All Pools: perform a recalculation between pool properties and object
  properties to determine which objects match and will be included in each of 
  the pools
  
- Run Service on All Pools in the Table:  run a Service or Workflow using all
  of the pools in the table as the combined set of execution targets. 
  
- Bulk Deletion:  delete all pools currently in the table.

## Device Pool Creation Example

![Device Filtering](../_static/inventory/pools/device_filtering.png)

This pool enforces the Union of the following conditions:

-   name: `Washington.*` \-\-- Match is Inclusion; all devices whose name begins
    with `Washington` will be selected
-   subtype: `GATEWAY|PEER` \-\-- Match is Regular Expression; all devices having
    subtype `GATEWAY` and `PEER` will be selected
-   vendor: `Cisco` \-\-- Match is Equality; all devices whose vendor is `Cisco`
    will be selected

In summary, all `Cisco` and `GATEWAY and PEER` devices whose name begins with
`Washington` will match these conditions and be included as members of the pool.

!!! note


    - All properties left with empty fields are simply ignored unless the `Empty`
      match option is selected and then that parameter is enforced to be empty.

    - Using the `Invert` checkbox reverses the logic for that parameter. So if 
      `Washington.*` is specified in the name field, `Invert` will cause all devices to 
      match whose name does NOT begin with `Washington`.

    - Along with all properties of a device, you can use the device's collected
      `Configuration` and `Operational Data` as a constraint for the pool. 

## Links Pool Creation Example

![Link filtering](../_static/inventory/pools/link_filtering.png)

This pool enforces the union of the following conditions:

- subtype: `Ethernet link` \-\-- Match is Equality; all Ethernet links will be
  selected
- source name: `Washington.*` \-\-- Match is Inclusion; all links whose source
  name includes `Washington` will be included

In summary, all `Ethernet Link`s starting with devices whose name includes
`Washington` will be members of the pool.

## Default Pools

Three pools are created by default in eNMS:

- `All objects`: A pool that matches all Devices and Links.
- `Devices only`: A pool that matches all Devices, no Links.
- `Links only`: A pool that matches all Links, no Devices.

## Pools Based on Configuration

Pools can be created by searching the configurations data collected from all of
the devices, rather than just the Inventory parameters for each device.
Configuration collection must be first configured, and then allowed to run at
least once before the configurations can be searched against for the Pool.

## Filter the View with a Pool

Pools can be used as filters for Devices and Links on the geographical
view: `Visualization -> Geographical View`. The first alphabetical pool in the list
will be displayed on the map by default, so make sure to create a smaller pool to
display as the default if your inventory is large. Use the pool selector at the top
to change the displayed devices and links.

![Pool filtering of the view](../_static/inventory/pools/view_filter.png)

## Use a Pool as target of a Service or a Workflow

In `Service Edit Panel -> Step 3`, select Device(s) and/or Pool(s) as target(s).

![Use a pool as a target](../_static/inventory/pools/target_pool.png)

## Use a Pool to restrict User Access or Credential Use

In `Administration -> Access` and `Administration -> Credentials`, the
administrator has the ability to restrict users.

## Pool Recalculation

All Pools are subject to automatic updates by eNMS (contingent upon the
fact that its \'Manually Defined\' flag is NOT set). Pool recalculations occur
after creation in the following cases:

- When the eNMS starts up or restarts
- When a device is manually added to the inventory (only for applicable
  pools)
- When a device is modified
- After pulling or cloning the content from the git configuration
  repository, and the applicable pool relies on `configuration` and/or 
  `operational data` parameter fields.
- When a service runs that has `Update pools before running` selected in
  `Step 3` of the service targets panel, only the target pools for that
  service are updated.
- When a service runs that has `Update all pools after running`, all pools
  are updated once that service terminates. 

To manually update a Pool:

- Click on the `Update` button of a desired pool in the 
  `Inventory -> Pool Management` table listing
- Click on the `Update all pools` button at the top of Pool Management panel

## Manual definition and `Manually Defined` option

Initially, by default, the devices and links within a pool are
determined based on the pool properties. First edit the pool and set
`Manually Defined` to enabled.  

![Manual definition of a pool](../_static/inventory/pools/manual_definition.png)

Next, the individual pools can be edited by the user clicking the hyperlink for
each device type:  device, link, user, service.  The table for that object
type's included members will be displayed. Click the `+` button at the top of
the table to add the object. The user can now select the devices to manually add
from the inventory list or paste a list of comma-separated devices from the
clipboard (however, all devices must be valid in the inventory).

![Manual definition of a pool](../_static/inventory/pools/manual_add.png)

Note that pools with manually selected objects MUST have the `Manually Defined`
checkbox selected. This prevents manually selected pools from being recalculated
based on pool criteria. If the user wants to run against a pool that has some
criteria specified as well as some manually specified devices, it is advised to
have 2 pools: one with the criteria specified, and another with the manually
selected devices. When running a service, multiple pools and multiple devices can
be specified, and the service will run against all specified objects.

