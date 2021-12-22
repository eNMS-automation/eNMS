Perform a GIT action on a set of files used or created by a workflow.

![GIT Action Service](../../_static/automation/builtin_service_types/git_action.png)

- `Path to Local Git Repository`

- `Path is relative to eNMS folder`

- `Git Pull`

- `Do 'git add' and commit`

- `Commit Message`

- `Git Push`

!!! note
    
    Any combination of the GIT actions are supported. If all are selected, the repo
    will first be pulled, then add/committed, and then pushed.