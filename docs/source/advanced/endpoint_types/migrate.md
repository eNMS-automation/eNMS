# Migrate Between Application Instances
Allows you to migrate the service from one application instance to another provided they are on the same release

**Method**: Post<br />
**Address**: /rest/migrate/export or /rest/migrate/import <br />
**Parameters**: None <br />
**Payload**: Pending

The body must contain the name of the project and the types of instances to
import/export. The import endpoint supports an additional boolean parameter
`empty_database_before_import` that controls whether to empty the database
before importing.

### Example Payload

```json
{
  "name": "test_project",
  "import_export_types": ["user", "group", "device", "file", "link", "service", "network", "workflow_edge", "task", "credential", "pool"],
  "empty_database_before_import": true
}
```

You can also trigger the import/export programmatically. Here's an
example with the python `requests` library.

```python
from requests import post
from requests.auth import HTTPBasicAuth

post(
    'yourIP/rest/migrate/import',
    json={
        "name": "Backup",
        "empty_database_before_import": False,
        "import_export_types": ["user", "group", "device", "file", "link", "service", "network", "workflow_edge", "task", "credential", "pool"],
    },
    headers={'content-type': 'application/json'},
    auth=HTTPBasicAuth('admin', 'admin')
)
```

-   Topology Import / Export

The import and export loads or stores a `.xls` file containing the topology.
This is triggered using a POST request to the following URLs:

    # Export: via a POST method to the following URL
    https://<IP_address>/rest/topology/export

    # Import: via a POST method to the following URL
    https://<IP_address>/rest/topology/import

For the import, attach the file as part of the request (of
type "form-data" not JSON). A boolean value for `replace` must also be
specified.

- `replace`: Whether or not to empty the database before the import

Example of python script to import programmatically:

```python
from pathlib import Path
from requests import post
from requests.auth import HTTPBasicAuth

with open(Path.cwd() / 'project_name.xls', 'rb') as f:
    post(
        'https://IP/rest/topology/import',
        json={'replace': True},
        files={'file': f},
        auth=HTTPBasicAuth('admin', 'admin')
    )
```

For the export, the name of the exported file must be set in the JSON
payload:

```json
{
    "name": "project.xls"
}
```