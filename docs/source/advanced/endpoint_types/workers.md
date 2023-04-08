# Get Worker Status
Show worker processes and services they're currently running. This endpoint will return an error response if redis is not used.

A successful response is in the format of 
```json
{
    <pid>: {
        "info": {
            "memory": <percent memory>%
        },
        "jobs": {
            <service name A>: <number currently running>,
            <service name B>: <number currently running>
        }
    }
}
```

Otherwise the response will look like
```json
{ "error": <error detail> }
```

**Method:** Get<br />
**Address:** /rest/workers <br />
**Parameters:** None <br />
**Payload:** None <br />

# Examples

## Typical response
```json
{
    "574677": {
        "info": {
            "memory": "1.1055756400082297%"
        },
        "jobs": {}
    },
    "574678": {
        "info": {
            "memory": "0.41382545141032046%"
        },
        "jobs": {
            "Basic Superworkflow": "1",
            "Data Processing Service": "3",
        }
    },
    "574680": {
        "info": {
            "memory": "0.9065742291978954%"
        },
        "jobs": {}
    }
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