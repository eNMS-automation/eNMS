from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import *
from wtforms.validators import optional

# nodes can be added to the database either one by one via the AddNode
# form, or all at once by importing an Excel or a CSV file.
class AddNode(FlaskForm):
    hostname = TextField('Hostname', [optional()])
    ip_address = TextField('IP address', [optional()])
    vendor_choices = (('Cisco',)*2, ('Juniper',)*2)
    vendor = SelectField('Vendor', [optional()], choices=vendor_choices)
    operating_system = TextField('Operating System', [optional()])
    os_version = TextField('OS version', [optional()])
    longitude = FloatField('Longitude', [optional()])
    latitude = FloatField('Latitude', [optional()])
    
class AddNodes(FlaskForm):
    validators = [FileAllowed(['xls', 'xlsx', 'csv'], 'Excel or CSV file only')]
    file = FileField('', validators=validators)
    
class DeleteNode(FlaskForm):
    nodes = SelectMultipleField('Nodes', choices=())
    
class AddLink(FlaskForm):
    source = SelectField('Source', choices=())
    destination = SelectField('Destination', choices=())