# Local Server CLI interface

The local instance terminal can be used as a CLI interface that interacts
with the eNMS application and supports the following operations:

## Run a service

If an eNMS service has been created on the application, the user can run a
service via this CLI Interface.

General syntax:

    `flask run_service <service_name> --devices <list_of_devices> --payload '{json dict}'`

Options:

    --devices = List of comma separated device names (Optional)
    --payload = JSON dictionary of key/values, serving as starting data
                for the service to be used later (Optional)

Examples:

    `flask run_service get_facts`
    `flask run_service get_facts --devices Washington,Denver`
    `flask run_service get_facts --payload '{"a": "b"}'`
    `flask run_service get_facts --devices Washington,Denver --payload '{"a": "b"}'`

## Delete old log entries

This command removes logs, changelogs or results. By default, logs older
than 15 days will be removed from their respective tables

General syntax:

    `flask delete_log --keep-last-days <value> --log <value>`

Options:

    --keep-last-days = Number of days to keep the logs (Optional: default to 15)
    --log = The log information to remove the logs from, either "changelog" or
            "result" (Required)

Examples:

    `flask delete_log --keep-last-days 10 --log result`    # Retains the last 10 days of result
    `flask delete_log --log changelog`                     # Retains the last 15 days of changelogs

## Refresh Network Configuration Data

The Network Configuration data can be gathered and then stored in a
central location, namely the git repository. eNMS can be used to fetch
the Network Configuration from git and have it stored locally in `network_data/`

General syntax:

    `flask pull_git`

Options:

    None

!!! note

    If trouble is experienced, ensure that

    - flask is being run from the correct directory, such as, is it installed
      inside a python virtualenv?
    - http_proxy, https_proxy, and NO_PROXY are set appropriately for your
      environment to allow the connection.