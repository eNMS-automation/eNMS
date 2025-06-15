# Get Worker Status

Show worker processes and services they're currently running. This endpoint will return an error response if redis is not used.

**Method**: Get <br />
**Address:**: /rest/workers <br />
**Parameters**: None<br />
**Payload**: None<br />

A successful response is in the format of

```json
{
    <server-name-pid>: {
 
        "admin_only":false,
        "current_run":<number>,
        "description":"",
        "id":<id>,
        "last_update": <date>,
        "name": <server-name-pid>,
        "owners":[],
        "process_id":<id>,
        "rba_read": [],
        "runs":[],
        "servers":{}
    }
}
```

Otherwise the response will look like

```json
{ "error": <error detail> }
```

# Examples

## Typical response

```json
{
   "app - 1515859": {
        "admin_only": false,
        "current_runs": 0,
        "description": "",
        "id": 89769,
        "last_update": "2024-11-16 05:19:12.637478",
        "name": "app - 1515859",
        "owners":[...],
        "process_id": 1515859,
        "rbac_read":[...],
        "runs":[...],
        "server": {...},
        "server_id":1,
        "server_name": "app",
        "server_properties": {
            "id": 1,
            "name": "app",
            "type": "server"
        },
        "subtype": "gunicorn",
        "type": "worker"
}
```

## Redis isn't being used

```json
{
    "error": "This endpoint requires the use of a Redis queue."
}
```

## No information available

```json
{
    "error": "No data available in the Redis queue."
}
```
