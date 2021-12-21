Service for sending REST CRUD (create, replace, update, delete) Http 
commands to a device that accepts them

![REST Call Service](../../_static/automation/builtin_service_types/rest_call.png)

Configuration parameters for creating this service instance:

- `Call Type` REST type operation to be performed: GET, POST, PUT, DELETE, PATCH
- `Rest Url` URL to make the REST connection to
- `Payload` The dictionary data to be sent in POST or PUT operation
- `Params` Additional parameters to pass in the request. From the
  requests library, params can be a dictionary, list of tuples or
  bytes that are sent in the body of the request.
- `Headers` Dictionary of HTTP Header information to send with the
  request, such as the type of data to be passed. For example,
  {\"accept\":\"application/json\",\"content-type\":\"application/json\"}
- `Verify SSL Certificate` If checked, the SSL certificate is
  verified. Default is to not verify the SSL certificate.
- `Timeout` Requests library timeout, which is the number of seconds
  to wait on a response before giving up
- `Username` Username to use for authenticating with the REST server
- `Password` Password to use for authenticating with the REST server

!!! note

    This service supports variable substitution (as mentioned in the
    previous section) in several of the input fields of its
    configuration form.
