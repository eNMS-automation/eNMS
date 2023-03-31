## Service Dependency

If a workflow contains parallel paths of execution, and one service must be
run after another service in another path, you can enforce that order
by configuring Priority in Step1 of the Service/Workflow Editor. One such
example is illustrated here:

![Service Dependency](../_static/automation/workflows/service_dependency.png)
 
Priority allows the user to determine the order a service runs when two
services would otherwise be run at the same time. The typical use case is
when a service has two edges exiting from the right side and both edges are
the same type. In this case the user may determine the order of the service
execution using Priority. The higher number gets run first.

## Restart Workflow From Here

Using the right-mouse-click menu, a workflow can be restarted from any
service as the "Entry point" and using the runtime payload from a
previous run. This is useful if:

- the user is testing a workflow with a lot of services.
- device targets fail unreliably and automation must be restarted at 
  unpredictable locations in the workflow and:
  
    a) services are not idempotent, meaning that it is not possible to
       re-run the same services on the devices without breaking, or:

    b) there is simply not enough time to re-run all the previous
       services.
  
Selecting `Restart Workflow from Here` by right clicking on a service 
presents the user with a form to select:

- `Restart Runtime`: The previous runtime to use as the payload for
  continuing the workflow. This defaults to the runtime that is currently
  displayed in the workflow builder.
- `Targets` gives several options for where to obtain device targets for
  the new run:
   
      - Manually defined:  Use the targets manually defined below.
      - Restart run: Use the targets from the selected restart runtime.
      - Workflow:  Use the targets that are currently defined at workflow level.
        
- `Devices`: for use with the `Manually defined` option above.
- `Pools`: for use with the `Manually defined` option above.

!!! note

    Variables, set to values that cannot be streamed as JSON, are not
    available to subsequent services after restarting the workflow. For
    example, if the user performed a set_var on a python function to allow
    it to be used in a subsequent service, this will not work after using
    `Restart Workflow from Here`.

## Disable a Service or Workflow

The `Disabled` property, when checked, prevents a workflow or service from
running from the UI or from the REST API.  This is useful when closed loop
automations that are triggered through the REST API by another system need
to be prevented from running. 

The `Disabled` property is accessed in the UI in the Step 1 Service / Workflow
Editor panel.  And when it is checked, the `Disabled Time & User` is captured
in the UI in a read-only field. The property can also be toggled via the REST
API instance endpoint `rest/instance/service` and passing a payload that looks
like:

```json
{
    "name": "service or workflow name",
    "devices": [""],
    "disabled": true
}
```

!!! note

    Disabling a service inside of a workflow prevents that service from running
    with the Right-Mouse-Click->Run option. It does not prevent that service
    from running when the entire workflow is run: use the Skip option to achieve
    that functionality instead.

## Connection Cache

When using netconf, netmiko, napalm, and scrapli services in a workflow,
eNMS will cache and reuse the connection automatically. In the Step2
`Connection Parameters` section of a service, there are some properties to
change this behavior :

- `Start New Connection`: **before the service runs**, the current
  cached connection is discarded and a new one is started.
    
- `Connection Name`: If changed to something other than `default`, the
  connection will be cached as a separate connection to that same device.
  This allows for multiple simultaneous "named" connections to a single
  device, as in this example:
  
![Service Dependency](../_static/automation/workflows/multiple_connection_workflow.png)  
    
- `Close Connection`: once the service is done running, the current
  connection will be closed.

## Waiting Times and Retries

Services and Workflows have a `Time to Wait` property: this tells eNMS
how much time it should wait after the service has run before it begins
the next service.

A service can also be configured to `Retry` in the event of a failure. 
Retries allow for a `Number of Retries`, `Time between retries`, `Max
number of retries` to be configured. 

The `Max number of retries` exists because it is possible for the user to
manipulate the `retries` variable in `post processing` section for service
results.  For example, the user could set additional retries in the event
of some condition, or perhaps if something is missing in the results, increase
retries by `1`.  This `Max number of retries` is settable to prevent an
infinite loop from occurring: once it is reached, the service will fail.

To demonstrate the relationship between retries and wait times, an example
execution of a service in a workflow is as follows:

    First try (failure)
    time between retries pause
    Retry 1 (failure)
    time between retries pause
    Retry 2  (Successful, or only 2 Retries specified)
    Waiting time pause

## Superworkflow

Just as a workflow can contain a subworkflow to subdivide and
encapsulate related functionality, a workflow can also designate a
superworkflow in `Step2`. The superworkflow allows for services to
be run before and after the main workflow and using a potentially
different workflow traversal mode (service by service or device by
device). 

Superworkflows function like a document template so that
activities common to all workflows can be performed. When the same
superworkflow is used by multiple main workflows, it behaves like a
shared service: a change to the superworkflow affects all workflows that
use it. 

In the superworkflow definition in Workflow Builder, the
position of the main workflow is designated by adding the `Placeholder`
service to the graph. And in the main workflow definition, the
superworkflow must be selected from the list of existing workflows.
