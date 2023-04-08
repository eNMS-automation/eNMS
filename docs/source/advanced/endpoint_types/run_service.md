# Run a Service

Initiate execution of a service passing in values to control its operation.

**Method**: Post <br />
**Address**: /rest/run_service <br />
**Parameters**: None <br />
**Payload**:

 - `name`: Name of the service.
 - `devices`: (default: `[]`) List of target device names. By default, the
     service will run on the devices configured on the service.
 - `pools`: (default: `[]`) Same as devices but for pools.
 - `ip_addresses`: (default: `[]`) Same as devices but using ip_addresses.
 - `async`: (default: `false`) boolean.
     -   `false`: eNMS runs the service and responds to your request
         when the service completes. The response contains
         the result of the service, but the connection might time out
         if the service takes too long to run.
     -   `true`: eNMS runs the service in a different thread and
         immediately responds with the service ID. (Recommended)
 - user_created: (optional) this could be list, dictionary, or string as
   desired. pass in as many as needed. (see user_identified_key & aid in
   example).

#
# Examples
## Run Service
```json
{
  "name": "my_service_or_workflow",
  "devices": ["Washington"],
  "pools": ["Pool1", "Pool2"],
  "ip_addresses": ["127.0.0.1"],
  "async": true,
  "user_identified_key": "user_identified_value",
  "aid": "1-2-3"
}
```

!!! Note
    - All targets are taken in aggregate; either those defined on the service
    or those passed to run_service endpoint are used. If any of `devices`,
    `pools`, or `ip_addresses` are specified no targets are used from the
    service.
    - For Postman, use the type `raw` for entering key/value pairs into
    the body. Body must also be formatted as application/JSON.
    - The optional user_created values can be accessed within the service by
    referencing `payload["your_variable_name"]`.
    - Try `log('info', payload)` in pre-processing to view the objects the
    service knows about. 

#
## Run Service Response - Synchronous

```json
{
  "runtime": "2020-04-28 12:21:11.404910",
  "success": true,
  "summary": {
      "success": [
          "Device1_Name",
          "Device2_Name"
      ],
      "failure": []
  },
  "duration": "0:00:01",
  "trigger": "REST",
  "devices": {
     ...
  },
  "errors": []
}
```


!!! Note
    - If the "async" argument is either false or omitted, then the request
     will block until the service has run to completion or is manually
     stopped.
    - This is a subset of the JSON response returned for a device-by-device
     workflow.
#
## Run Service Response - Asynchronous

```json
{
   "errors": [],
   "runtime": "2020-04-28 12:16:45.201077"
}
```
!!! Note
    -  If the "async" argument is true, then the JSON response contains the
       runtime name needed to retrieve the results.