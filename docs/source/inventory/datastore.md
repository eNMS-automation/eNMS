---
title: Data Store
---

# Overview

The Data Store serves as the central repository for all data managed by the application. It supports various data types, including text, secret values, JSON objects, spreadsheets, and DCIM/IPAM-related data such as IP addresses, VLANs, and cables.

A Store represents a table within the Data Store. Navigating the Data Store works like browsing a file system. The current path of nested Stores is displayed as a sequence of hyperlinks, each linking to its respective Store in the hierarchy.

## Data Type of a Store

Each Store has a `data_type` property that defines the kind of data it contains (for example, a Store for IP addresses will contain only IP address data).

A Store is also a type of Data and may include other Stores if its `data_type` is set to "store", similar to folders containing subfolders.

The Data Type of a Store can only be set when the Store is created. Once created, this property becomes read-only.

A Data object can only be moved to another Store with the same Data Type (for example, data of type A can only belong to a Store whose `data_type` is also A).

## Persistent ID

Every data object has a persistent ID. This ensures that data can be consistently referenced within workflows and across software releases, even when the data is renamed (or the database ID modified).
Users can copy the persistent ID directly from the Data Store table using the provided copy-to-clipboard button.

## Reference a Data object in a workflow

The `get_data` global function in the Workflow Builder retrieves a data object in python, either by its path or by its persistent ID.

## Examples

The following features have been implemented to demonstrate the capabilities of the datastore:

- **New JSON object type**
    - A JSON object has a `value` property to store JSON data.
    - A JSON object can be edited directly from the edit panel.
    - A JSON object can be downloaded as a JSON file from the JSON table.

- **Example models**
    - **VLAN model** :  demonstrates the **Get Next in Sequence** mechanism: a button is added next to the *VLAN ID* field in the form that automatically fills the field with the next available VLAN ID when clicked. That button is implemented with the `layout` keyword argument to customize the layout of a field.
    - **Port model** :  shows a SQL relationship with an internal eNMS model (`Device`).
    - **Cable model** :  demonstrates SQL relationships with a custom datastore model (`Port`).

# Adding a new model to the Data Store

New models can be added when needed. To define a new model:
- Create a subclass of `Data` with your custom properties.
- Save the file in the `models / datastore` directory.
- Define the corresponding UI table in JavaScript within the `static / js / datastore` directory.

## Python file

- In the `models / datastore` folder, add a new python file to define the database model and its associated form.

```
from eNMS.database import db
from eNMS.forms import DataForm
from eNMS.fields import HiddenField, InstanceField
from eNMS.models.administration import Data

class Example(Data):
    __tablename__ = "example"
    pretty_name = "ISO Address"
    __mapper_args__ = {"polymorphic_identity": "example"}
    id = db.Column(Integer, ForeignKey("data.id"), primary_key=True)


class ExampleForm(DataForm):
    form_type = HiddenField(default="example")
    store = InstanceField(
        "Store", model="store", constraints={"data_type": "example"}
    )
```

## Javascript File

- In `static / js / datastore`, add a new JS file with the table code:

```
import { tables } from "../table.js";

tables.example = class extends tables.data {};
tables.example.prototype.type = "example";
```

## Update to properties.json

- In `setup / properties.json` under the `tables` key, add the table properties:

```
    "example": [
      {
        "data": "scoped_name",
        "title": "Name",
        "search": "text",
        "width": "200px"
      },
      {
        "data": "creator",
        "title": "Creator",
        "search": "text",
        "visible": false
      },
      {
        "data": "description",
        "title": "Description",
        "search": "text",
        "orderable": false
      },
      {
        "data": "creation_time",
        "title": "Creation Time",
        "search": "text",
        "visible": false
      },
      {
        "data": "buttons",
        "width": "130px",
        "orderable": false,
        "export": false
      }
    ],
```
