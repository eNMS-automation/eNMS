# Workers

A worker corresponds to a UNIX process used for running services, with each worker being associated with a server.

<h4>Workers Details</h4> 
![Worker Details](../_static/administration/worker.png)

* **Name**: Name of the worker - defaults to "Server Name - Process ID"
* **Process ID**: Unix Process ID (obtained with os.getpid)
* **Description**: Text field for storing notes 
* **Subtype**: Specifies the application that spawned the worker. The subtype is determined by the "_" environment variable, which varies based on the deployment method. Common values include "python3" "gunicorn" or "dramatiq".
* **Last Update**: The last time the worker was updated (and used to run a service)

Note:
- When the application starts, it checks if the server's workers are running on Unix (via /proc/id). If they are not, they are deleted from the database.
- A worker is detected (and created or updated) whenever a job starts running. By default, until the first service is run, there isn't any worker in the database.
- The worker's name is set to "Server Name - Process ID" to ensure uniqueness across servers.
- The "get_workers" REST endpoint can be called to retrieve information about each worker.
- When a worker is deleted from the worker table, the application sends a SIGTERM signal to the underlying Unix process.
