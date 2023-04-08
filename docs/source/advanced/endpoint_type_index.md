# REST API Index

In this section, the word `instance` refers to any object type supported
by eNMS. In a request, `<instance_type>` can be any of the following:
`device`, `link`, `user`, `service`, `task`, `pool`, `result`.



- [Retrieve an instance](endpoint_types/retrieve_instance.md) 
  Returns the attributes of an existing instance.
- [Delete an instance](endpoint_types/delete_instance.md) 
  Deletes an instance.
- [Create or update an instance](endpoint_types/create_update_instance.md) 
  Builds or modifies existing instance.
- [Retrieve a list of instances - simple](endpoint_types/retrieve_list_instance_simple.md) 
  Using a simple GET where filter criteria easily fit into the URL to return a
  list of instances that match criteria with set attributes.
- [Retrieve a list of instances - custom](endpoint_types/retrieve_list_instance_custom.md) 
  Using a POST, this endpoint provides all the filtering functionality found in
  the user interface, allowing selection of the return attributes plus enhanced
  filtering.
- [Run a service](endpoint_types/run_service.md) 
  Run an existing service.
- [Get status or results of service](endpoint_types/results_service.md) 
  Return results of a completed service, or the status of a service if
  currently running.
- [Retrieve device configuration](endpoint_types/device_config.md) 
  Returns the device configuration stored for a device. 
- [Migrate between applications](endpoint_types/migrate.md) 
  Provides import/export functionality to migrate data between eNMS instances.
- [Ping application](endpoint_types/ping.md) 
  Tests whether the application is running and responding.
- [Get worker stats](endpoint_types/workers.md) 
  Get information of workers and currently running services.
- [Administrative](endpoint_types/admin.md) 
  Provides access to many endpoints found in the administration panel.


  









