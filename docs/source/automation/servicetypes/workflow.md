This a placeholder for the ability to add a subworkflow to an existing
workflow as a service.

![Subworkflow Service](../../_static/automation/builtin_service_types/workflow.png)

Configuration parameters include:

`Close Connection`: Once the subworkflow is done running, the current
  connection will be closed.
  
`Superworkflow`:  Select from a workflow from the list that will act as a 
  superworkflow.  The superworkflow must have added the `placeholder`
  service to indicate when this workflow will execute.