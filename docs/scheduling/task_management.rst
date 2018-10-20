=========
Scheduler
=========

eNMS uses APScheduler to run Services and Workflows. Primary features of the scheduling system are:
- Service instance tasks will run in parallel to other service instance tasks as long as they are standalone and do not exist within a workflow.
- Service Instance tasks (and workflow instance tasks) that exist inside of a workflow will run in sequential order as defined in the workflow builder.
- If multiple inventory devices are selected within the workflow instance definition, these will run independently from each other, in parallel, while following the sequential rules of the workflow. Status of the workflow will be displayed in the workflow builder. 
- If multiple inventory devices are selected within the individual service instance definitions (but not at the workflow instance level, since that overrides any devices selected for the individual service instances), these will run in parallel, but each service instance step is required to be completed by all devices before moving to the next step in the workflow and both Task Status and the Current Task step are displayed in the workflow builder