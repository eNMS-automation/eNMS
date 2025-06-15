# Add instances to a relationship

Add instances to an object's relationship using their names.

**Method**: Post<br />
**Address**: /rest/add_instances_in_bulk <br/>
**Parameters**: None<br />
**Payload**: A dictionary with the following key/value pairs:

- `target_type`: The type of object to update

- `target_name`: The name of the object to update

- `property`: The property (relationship) to update

- `model`: The type of object associated with the property

- `names`: A list of comma-separated names to add to the relationship (property)

### Example Payload

```
{
    "target_type": "service",
    "target_name": "service_name",
    "property": "target_devices",
    "model": "device",
    "names": "name1,name2"
}
```

### Example of return

```
{
    "number": 1,
    "target": {
        "id": 13892,
        "name": "test email list issue",
        "report_format": "text",
        "scoped_name": "test email list issue",
        "type": "workflow"
    }
}
```
