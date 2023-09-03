# Retrieve a List of Instances - Custom
This endpoint provides 
control over which columns to return, the types of matching, the sort
order of returned items, and the max number of returned items. This
search operates with the same filtering options available within the user
interface on each table.

**Method**: Post<br />
**Address**: /rest/search<br />
**Parameters**: None<br />
**Payload**: A dictionary with the following key/value pairs:

 - `type`: Instance type of objects to search

      -   'device', 'link', 'user', 'service', 'task', 'pool', 'result'.

 - `columns`: List of attributes desired or used for filtering

      -   Possible values can be found in `setup/properties.json`,
          but generally correspond to user interface table headings.

 - `search_criteria`: OPTIONAL -  Similar to what is found in the user
   interface for filtering instance tables. The first bullet is for all
   instances, and the second bullet is for services only.

     1. Dictionary with column search criteria and search type info.
        - `<column-name>:<search-criteria>`: Column name as the key and
          the desired search criteria as the value.
        - `<columns-name>_filter:<filter_type>`: Use the column name with 
          '_filter' appended as the key.  The value specifies one of the 
          following filter types `regex`, `inclusion`, `equality`, `empty`.
        - Use multiple key key_filter pairs to filter on more than one
          column.

     2. Retrieve all results of a workflow including all sub-workflows
        (only for `result` instances).
        - `parent_service_name`: Name of top-level service.
        - `parent_runtime`: Time of service run.

 - `order`: OPTIONAL -  Allows sorting based on one of the values
     provided column.

      -   The expected format is `[{"column": 0, "dir": "asc"}]`.
      -   The value of `column` is the integer index of the
          `columns` list.
      -   The value for `dir` can be either "desc" for descending
          or the default "asc" for ascending.

 - `maximum_return_records`: OPTIONAL - Integer indicating the
     maximum number of records to return.
 - `start`: OPTIONAL - Integer indicating the first record to be
     returned, which can be used with `maximum_return_records` to implement
     paging. 
     
#
# Examples
## Search Devices

```json
{
  "type": "device",
    "columns": ["name", "ip_address", "configuration", "configuration_matches"],
    "maximum_return_records": 3,
    "search_criteria": {
      "configuration_filter": "inclusion",
      "configuration": "loopback"
    }
}
```
!!! Note
     Special columns “matches” is derived from a regex match object which
     returns the line where a regex was found.

#
## Search Links
```json
{
  "type": "link",
    "columns": ["name", "source_name"],
    "maximum_return_records": 3,
    "search_criteria": {
      "name_filter": "inclusion",
      "name": "name_of_link"
    }
}
```
#
## Retrieve the latest result of a workflow
```json
{
  "type": "result",
  "columns": ["parent_runtime", "result"],
  "maximum_return_records": 1,
  "search_criteria": {
    "workflow_name_filter": "inclusion",
    "workflow_name": "the_name_of_workflow"
  },
  "order": [{"column": 0, "dir": "desc"}]
}
```
#
## Retrieve specific runtime of a top-level workflow, include all children results, and include paging
```json
{
  "type": "result",
  "columns": ["result", "parent_runtime", "service_name"],
  "maximum_return_records": 1,
  "search_criteria": {
    "parent_runtime": "2021-04-19 04:09:05.424206", 
    "parent_service_name": "your_workflow"
  },
  "start": 1,
  "maximum_return_records": 100 
}
```