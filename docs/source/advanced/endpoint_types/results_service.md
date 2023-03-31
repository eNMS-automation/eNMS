# Get the Status or Results of a Service

Return results of a completed service, or the status of a service if currently running.

**Method:** Get<br />
**Address:** /rest/result/`service_name`/`runtime` <br />
**Parameters:** None<br />
**Payload:** None<br />

!!! Note
    - The `service_name` must be URL encoded.  This replaces spaces and
      special characters with %<number>.  For example a space becomes '%20'.
    - The status property in the result will show either "Running" or "Completed".
    - Before the service has started the request fails with the HTTP 404 error
      indicating that the service run is not found.

#
# Examples
## Get run service result response - result not ready yet

```python
{
    "status": "Running",
    "result": "No results yet."
}
```
!!! Note
    The response when the result is ready will look very close to the
    synchronous result, above - but nested one level deeper inside the
    "result" property, as below.

#
## Get run service result - result is ready
```json
{
    "status": "Completed",
    "result": {
        "runtime": "2020-04-28 12:47:43.492570",
        "success": true,
        "summary": {
            "success": [
                "Device1_Name",
                "Device2_Name"
            ],
            "failure": []
        },
        "duration": "0:00:02"
    }
}
```
