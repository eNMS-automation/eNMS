# Add a new property to the model

- Open /eNMS/source/objects/models.py and add a Column to the appropriate model (Object, Node or Link)
Example: description = Column(String) in the Object class.
- Open /eNMS/source/objects/properties.py and add the property in the appropriate tuple.
- Open /eNMS/source/base/properties.py and add the property and it's user-friendly name in the "pretty_names" dictionnary.
- (Optional) If you want the new property to be displayed as a diagram in the dashboard, open /eNMS/source/objects/properties.py and add the property in the appropriate diagram tuple.
- Delete the database.db file, and restart the application.
