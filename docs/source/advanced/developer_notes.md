---
title: Developer Notes
---

Best Practices and examples. Including:

::: {.contents local="" depth="1"}
:::

# Python Examples

## Accessing Devices when Using Pools

``` python
result = []

for pool in workflow.pools:
  for device in pool.devices:
    result.append((device.name, device.ip_address))

results["success"] = True
results["result"] = result
```

## Accessing Inital Payload and Set Variable

``` python
upgrade_from = payload.get("upgrade_from")
upgrade_to = payload.get("upgrade_to")
upgrade_file = payload.get("upgrade_file")

if not (upgrade_from and upgrade_to and upgrade_file):
    save_result(success=False,
                       result={"error": "The workflow initial payload must define: upgrade_from, upgrade_to, and upgrade_file"},
                       exit=True)

set_var("upgrade_from", upgrade_from)
set_var("upgrade_to", upgrade_to)
set_var("upgrade_file", upgrade_file)

save_result(success=True, result={"upgrade_from": upgrade_from, "upgrade_to": upgrade_to, "upgrade_file": upgrade_file})
```

# Async Commands

Most commands display output and then the user gets a new command
prompt. Asynchronous commands trigger background behavior that continues
after the command completes and the user is presented with a new command
prompt.

Two basic strategies can be used for asynchronous commands:

1.  Issue the command in one service and then in the next service
    repeatedly check on the completion status.
2.  Issue the command and wait for either a timeout or wait for a
    completion message.

## Repeated Checks for Completion in Another Service

In this scenario, one service triggers an activity that will take some
time, for example a restart. A followup service can then be used with
retries to wait for completion.

The first service triggers some activity. Specify a delay for this
service so it will wait before moving on to the next service to start
testing for completion.

The second service watches for completion and succeeds when the desired
state is detected. Set the number of retries and the time between
retries to control how long and how often it will check for completion.
This service will terminate successfully if any retry completes with a
success=True, and will fail if all retries are exhausted without a
successful completion.

## Wait for Timeout or a Specific Completion Message

By default the Netmiko Validation service issues the command and waits
for either a new prompt or a timeout. The default timeout is 10 seconds.
Asynchronous commands might provide some output, but they complete and
return the user to a new command prompt before the requested activity is
complete. In this case, you must specify a different string to wait for
and disable waiting for the prompt.

These parameters are controlled in the Advanced Netmiko Parameters
section:

1.  The Expect String tells the service when to stop listening for
    command output. It is treated as a regular expression and also
    supports variable substitution. Also see Wait for Multiple Output
    Strings
2.  Auto Find Prompt controls whether the service will stop listening
    for command output when it sees a command prompt. Uncheck this to
    monitor output after the prompt is displayed.

The Cisco MSE command \"install add source \<destination> \<package>\"
has the following output: .. code-block:: python

> RP/B0/CB0/CPU0:PRSNCS01-IE1# install add source harddisk:/
> ncs6k-iosxr-7.0.1-base.tar Wed Nov 27 17:24:52.851 UTC Nov 27 17:24:54
> Install operation 142 started by ienapdev: install add source
> harddisk:/ ncs6k-iosxr-7.0.1-base.tar Nov 27 17:24:56 Install
> operation will continue in the background RP/B0/CB0/CPU0:PRSNCS01-IE1#
> Nov 27 17:29:27 It is a NO IMPACT OPERATION as all packages have
> already been added Nov 27 17:29:29 Install operation 142 finished
> successfully

In this case there was no work to do, but the command can take up to 10
minutes to complete. The following values were used:

1.  Timeout: 600
2.  Expect String: finished successfully
3.  Auto Find Prompt: Unchecked (false)

# Wait for Multiple Output Strings

The Netmiko Validation service typically waits for the next prompt to
stop listening for new command output. The Expect String parameter in
Advanced Netmiko Parameters specifies an alternate termination string.
We\'ll match multiple strings by leveraging the fact that the Expect
String is actually a regular expression (regex).

Regular expressions use the pipe character \| as an \"or\" operator
(more formally known as conjugation). The regex \"AB\" matches any
string that contains the two letters \"AB\". We can expand this to match
\"AB\" or \"CD\" using the regex \"ABb\|c\" matches any of the three.
You can use the handy site <http://regex101.com> to test out your
expressions during development.

Note that by default Auto Find Prompt is enabled and will stop listening
for new output when the prompt is returned. Disable Auto Find Prompt to
wait for only the Expect String to match.

## Matching Multiple Success Strings

For example, if a copy command completes with \"finished successfully\"
but returns \"already exists\" if the file already exists. You can then
use the Expect String \"finished successfully\|already exists\" and know
that the file is there on the box.

## Matching Both Success and Failure Strings

The Expect String tells NetMiko when to stop listening for new output.
You can include both success and failure messages in the regex to catch
them quickly, but a little more is required to determine whether it\'s a
success or failure.

Given a command that returns a sunny day message \"finished
successfully\" or a variety of failure messages all preceded by
\"ERROR!\", we can use the Expect String \"finished
successfully\|ERROR!\" to catch both success and failure messages. If
the expression matches, then the service will return success. A little
python post-processing is required to force the service to fail on
error:

**Fail service if error string is found in output**

``` python
if "ERROR!" in results["result"]:
   results["success"] = False
   results["error"] = "An error occurred - see output"
```

With a little more work you can include the actual error line in your
result.

**Fail the service and return the actual error**

``` python
for line in results["results"].splitlines():
    if "ERROR!" in line:
        results["success"] = False
        results["error"] = line.strip()
        break
```

# Post Processing

Python Postprocessing allows the developer to execute Python code after
the service or workflow has completed, but before validation. This is
typically used to update the result for checking in the validation phase
or to perform more complex validation than is possible without code.
Postprocessing can also be used to recover from certain types of errors
in the service or workflow.

The following are best practices for Python Postprocessing code:

## Preserve Service Results

Most services create a results\[\"result\"\] that is useful as a
reference. If you know that the result is a dictionary, you can always
add information to that dictionary in postprocessing. Otherwise, save
additional information on results itself. Feel free to add additional
keys to the results structure. Common keys are \"message\" and
\"errors\". It can also be helpful to use a self explanatory key name
like \"Down RIs\" or \"Missing files\", and supply a list as the value.

## Stop on Service Errors

Usually you\'ll want to fail immediately if the service itself has
failed, this prevents any risk of overwriting useful debug information
and ensures that those looking at the failure see the actual error. Add
the following line to the top of each postprocessing script to stop if
the service itself failed:

``` python
if not results["success"]: exit()
```

# Run Method Relationships

+--------+-----------+-------------------------------------------------+
| Parent | Child Run | Description                                     |
| Run    | Method    |                                                 |
| Method |           |                                                 |
+========+===========+=================================================+
| Devi   | >         | > Child service will run for every device in    |
| ce by  | Service - | > parent workflow, using parent target.         |
| Device | > Once    |                                                 |
|        | > Per     | \-\-\-\-\-\-\-\-\                               |
| :      | > Device  | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|   -    |           | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|   -    | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|   -    | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|   -    | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+ |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ | :   Child service will run for every device in  |
|        | -\-\-\-\- |     parent workflow, using parent target.       |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\--+ | \-\-\-\-\-\-\-\-\                               |
|        |           | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | :         | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | Service - | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        |     Run   | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |     Once  | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        |           | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+ |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ | :   Child workflow will run for every device in |
|        | -\-\-\-\- |     parent workflow, using parent target.       |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- | \-\-\-\-\-\-\-\-\                               |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | -\-\-\--+ | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |           | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | :   Sub-W | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | orkflow - | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        |           | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |    Device | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+ |
|        |     by    |                                                 |
|        |           | :   Child workflow will run for every device in |
|        |    Device |     parent workflow, using parent target.       |
|        |           |                                                 |
|        | \-\-\-\-\ | \-\-\-\-\-\-\-\-\                               |
|        | -\-\-\-\- | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | \-\-\-\-\ | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | -\-\-\-\- | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | \-\-\-\-\ | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | -\-\-\-\- | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | \-\-\-\-\ | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | -\-\-\-\- | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | \-\-\-\-\ | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | -\-\-\-\- | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+ |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\--+ | :   Child workflow will run for every device in |
|        |           |     parent workflow, using child targets.       |
|        | :   Sub-W |                                                 |
|        | orkflow - |                                                 |
|        |           |                                                 |
|        |   Service |                                                 |
|        |     by    |                                                 |
|        |           |                                                 |
|        | Service - |                                                 |
|        |           |                                                 |
|        |  Workflow |                                                 |
|        |           |                                                 |
|        |   targets |                                                 |
|        |           |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\--+ |                                                 |
|        |           |                                                 |
|        | :   Sub-W |                                                 |
|        | orkflow - |                                                 |
|        |           |                                                 |
|        |   Service |                                                 |
|        |     by    |                                                 |
|        |           |                                                 |
|        | Service - |                                                 |
|        |           |                                                 |
|        |   Service |                                                 |
|        |           |                                                 |
|        |   Targets |                                                 |
+--------+-----------+-------------------------------------------------+
| S      | >         | > Child service will run for every device in    |
| ervice | Service - | > parent workflow, using parent target. All     |
|  by Se | > Once    | > devices must complete service to move         |
| rvice  | > Per     | > forward.                                      |
| - Work | > Device  |                                                 |
| flow T |           | \-\-\-\-\-\-\-\-\                               |
| argets | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
| :      | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|   -    | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|   -    | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|   -    | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+ |
|   -    | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ | :   Child service will run only once.           |
|        | -\-\-\--+ |                                                 |
|        |           | \-\-\-\-\-\-\-\-\                               |
|        | :         | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | Service - | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |     Run   | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        |     Once  | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |           | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | \-\-\-\-\ | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | -\-\-\-\- | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | \-\-\-\-\ | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | -\-\-\-\- | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+ |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- | :   Child workflow will process devices         |
|        | \-\-\-\-\ |     individually, for each device group that    |
|        | -\-\-\-\- |     made it to child in parent workflow. Number |
|        | \-\-\-\-\ |     of parent targets and multiprocessing       |
|        | -\-\-\-\- |     settings will affect how many devices are   |
|        | \-\-\-\-\ |     in a group.                                 |
|        | -\-\-\--+ |                                                 |
|        |           | \-\-\-\-\-\-\-\-\                               |
|        | :   Sub-W | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | orkflow - | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |           | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        |    Device | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |     by    | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        |           | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |    Device | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        |           | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+ |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ | :   Child workflow will process devices service |
|        | -\-\-\-\- |     by service, for each device group that made |
|        | \-\-\-\-\ |     it to child in parent workflow. Number of   |
|        | -\-\-\-\- |     parent targets and multiprocessing settings |
|        | \-\-\-\-\ |     will affect how many devices are in a       |
|        | -\-\-\-\- |     group.                                      |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- | \-\-\-\-\-\-\-\-\                               |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | -\-\-\--+ | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |           | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | :   Sub-W | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | orkflow - | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        |           | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |   Service | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        |     by    | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |           | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+ |
|        | Service - |                                                 |
|        |           | :   Child workflow will run using child         |
|        |  Workflow |     targets, for each device group that made it |
|        |           |     to child in parent workflow. Number of      |
|        |   targets |     parent targets and multiprocessing settings |
|        |           |     will affect how many devices are in a       |
|        | \-\-\-\-\ |     group.                                      |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\--+ |                                                 |
|        |           |                                                 |
|        | :   Sub-W |                                                 |
|        | orkflow - |                                                 |
|        |           |                                                 |
|        |   Service |                                                 |
|        |     by    |                                                 |
|        |           |                                                 |
|        | Service - |                                                 |
|        |           |                                                 |
|        |   Service |                                                 |
|        |           |                                                 |
|        |   Targets |                                                 |
+--------+-----------+-------------------------------------------------+
| Servic | >         | > Child service will run for every device using |
| e by S | Service - | > child targets.                                |
| ervice | > Once    |                                                 |
|  - Ser | > Per     | \-\-\-\-\-\-\-\-\                               |
| vice T | > Device  | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
| argets |           | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
| :      | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|   -    | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|   -    | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|   -    | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+ |
|        | -\-\-\-\- |                                                 |
|   -    | \-\-\-\-\ | :   Child service will run only once.           |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ | \-\-\-\-\-\-\-\-\                               |
|        | -\-\-\--+ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        |           | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | :         | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | Service - | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |     Run   | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        |     Once  | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |           | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | \-\-\-\-\ | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | -\-\-\-\- | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+ |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- | :   Child workflow will process devices         |
|        | \-\-\-\-\ |     individually, using child targets.          |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ | \-\-\-\-\-\-\-\-\                               |
|        | -\-\-\-\- | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | \-\-\-\-\ | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | -\-\-\-\- | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | \-\-\-\-\ | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | -\-\-\--+ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        |           | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | :   Sub-W | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | orkflow - | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        |           | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+ |
|        |    Device |                                                 |
|        |     by    | :   Child workflow will process devices service |
|        |           |     by service, using child targets.            |
|        |    Device |                                                 |
|        |           | \-\-\-\-\-\-\-\-\                               |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\- |
|        | -\-\-\-\- | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\ |
|        | \-\-\-\-\ | -\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+ |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ | :   Child workflow will process devices service |
|        | -\-\-\--+ |     by service, using grand-children targets.   |
|        |           |                                                 |
|        | :   Sub-W |                                                 |
|        | orkflow - |                                                 |
|        |           |                                                 |
|        |   Service |                                                 |
|        |     by    |                                                 |
|        |           |                                                 |
|        | Service - |                                                 |
|        |           |                                                 |
|        |  Workflow |                                                 |
|        |           |                                                 |
|        |   targets |                                                 |
|        |           |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\-\- |                                                 |
|        | \-\-\-\-\ |                                                 |
|        | -\-\-\--+ |                                                 |
|        |           |                                                 |
|        | :   Sub-W |                                                 |
|        | orkflow - |                                                 |
|        |           |                                                 |
|        |   Service |                                                 |
|        |     by    |                                                 |
|        |           |                                                 |
|        | Service - |                                                 |
|        |           |                                                 |
|        |   Service |                                                 |
|        |           |                                                 |
|        |   Targets |                                                 |
+--------+-----------+-------------------------------------------------+

# Custom Logger

Logging provides a way for the user to send information to the workflow
result log, the system changelog and to external files or systems. 
Custom loggers provide the connection to external files or systems and
must be configured by an administrator. Log calls can be made from
anywhere in the application that allows for Python statements: Pre and
Post processing and using the Python Snippet Service.

## Syntax

> log(severity, message, device=None, app_log=False, logger=None)

## Description

severity:

:   Required, string. Valid values, in escalating priority order:
    'info', 'warning', 'error', 'critical'

message:

:   Required, text. Custom log verbiage

device:

:   Optional, default=None. Associate log message to a specific device

app_log:

:   Boolean: Optional, default=False. The user controls whether log
    message is sent to changeling and/or specified destination

logger:

:   Optional, default in Results Log. When specified, log message is
    sent to the specified logger 

## Example:

``` python
log('info', 'message')              # Log message to the results logqq
log('info', 'message')              # Log message to the results log
log('error', 'message', logger="mylogger")   # Log an error message to the custom logger "mylogger"
log('info', 'message', app_log=True)         # Log message to both the results and change logs
log('warn', 'message', device=device.name, logger='my logger')  # Log an error message, associate to a device and send to the custom logger "mylogger"
```

# Exporting logs and data to SPLUNK

## SPLUNK event/message format

[Custom Logger](#custom-logger) can be configured to send logs to SPLUNK
and therefore can be utilized to export any kind of events and data into
SPLUNK. SPLUNK is a versatile and powerful data visualization and data
analysis platform. It is recommended to utilize SPLUNK for any types of
reporting.

Even though SPLUNK indexes data regardless of format, the best practice
is to submit data to splunk is by `key=value` pairs. Logger in iEN-AP is
configured to add time stamp and service name to every event exported to
SPLUNK. The rest of information will have to be added to event in
`key=value` format

## Example of an iEN-AP event received in SPLUNK

    5/20/20 2:48:36.000 PM <14>logtype="workflow" USER v548556 - SERVICE TACACS config exists - workflow="Provision TACACS on Cisco NCS4216" device="WORNNJWO-0330324A" note="Unable to login" action="end"

All the fields and values in the event text up to \"workflow\" are added
by iEN-AP. The rest of the event payload in form of key-value pairs was
added as payload from workflow:

    workflow="Provision TACACS on Cisco NCS4216"
    device="WORNNJWO-0330324A"
    note="Unable to login"
    action="end"

## Example of python lines that generated events from a workflow

``` python
log('info', f'workflow="{workflow.name} device="{device.name}" result="Error while getting configuration" action="end"', logger='splunk')
log('info', f'workflow="{workflow.name} device="{device.name}" result="Unable to login" action="end"', logger='splunk')
log('info', f'workflow="{workflow.name} device="{device.name}" result="Welp, nothing works" action="end"', logger='splunk')
```

::: note
::: title
Note
:::

SPLUNK parses key/value pairs as key=\"value\", where the key is not
enclosed in quotes but the value is
:::

**Recommended keys to use in every event**:

:   -   `workflow` - name of the workflow
    -   `device` - name of the device being processed

All other provided `key=value` pairs will be used as metrics and
dimensions in SPLUNK reports and dashboards.

## Example of report generated in SPLUNK based on logged data

![Example of SPLUNK report based on generated logs](../_static/advanced/developer_notes/splunk_report_example.png){.align-center}

# Command line search

**iensearch.py** is command line utility to search through collected by
iEN-AP configuration data. The tool is intended for use on remote
servers and provides a command line interface to iEN-AP data.

## Command line parameters

iensearch.py `[-h]` `[-A X]` `[-D]` `[-F X [X ...]]` `[-L]`
`[-O {screen,csv,json,python}]` `[-S X]` `[-U X]` `[-d X]` `[-i IP]`
`[-m X]` `[-o OS]` `[-s X]` `[-t SUBTYPE]` `[-se]` `[-sa]` `[-sv]`
`[-v VENDOR]`

**Program options**:

:   -   `-h`: Display help
    -   `-D`: Enable debug information during run
    -   `-F X [X ...]`, `--fields X [X ...]`: List of fields to be
        included in search result. Full list: `address`, `alt_id`,
        `city`, `console1`, `console2`, `configuration_matches`,
        `description`, `device_status`, `fqdn`, `icon`, `id`,
        `ip_address`, `last_duration`, `last_failure`, `last_modified`,
        `last_runtime`, `last_status`, `last_update`, `latitude`,
        `location`, `longitude`, `model`, `name`, `napalm_driver`,
        `nat`, `neat`, `netmiko_driver`, `network`, `operating_system`,
        `os_version`, `port`, `state_province_region`, `subtype`,
        `type`, `username`, `vendor`, `vpns`, `zip_postalCode`
    -   `-L`, `--list-only`: List devices matching specified search
        criteria. Do not include matched results
    -   `-O {screen,csv,json,python}`,
        `--output {screen,csv,json,python}`: Specify output format
    -   `-S X`, `--search X`: Search for text or regex inside
        configuration data
    -   `-U X`, `--url X`: API URL. Default is
        **https://ien-ap.verizon.com/rest/search**

**Search options**:

:   -   `-d X`, `--device X`: Name, part of device name or regex to
        match device name
    -   `-i IP`, `--ip IP`: Device ip address
    -   `-m X`, `--model X`: Device model
    -   `-o OS`, `--os OS` : Device operating system
    -   `-s X`, `--status X`: Device status. Example:
        `account verified`, `verified`
    -   `-t x`, `--subtype x`: Device subtype. Example: `UT`, `NGPON2`
    -   `-v X`, `--vendor X`: Device vendor filter

::: note
::: title
Note
:::

Regex is accepted in most text search arguments (MySQL style regex)
:::

## Examples of command line search

Search for `Loopback10` in configuration of `NCS 540` devices models and
output name (included by default), device ip and found text:

    iensearch.py --model="NCS 540" -S "Loopback10" -F ip_address configuration_matches,last_update

List of all Cisco 4202 devices. If no `-S` option specified only list of
device provided:

    iensearch.py --model="NCS 4202"
