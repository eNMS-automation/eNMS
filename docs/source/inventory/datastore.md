---
title: Data Store
---

# Data Store

## Overview

## Adding a new model to the Data Store

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

- In `static / js / datastore`, add a new JS file with the table code:

```
import { tables } from "../table.js";

tables.example = class extends tables.data {};
tables.example.prototype.type = "example";
```

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
