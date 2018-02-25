from flask_wtf import FlaskForm
from wtforms import *

class SyslogServerForm(FlaskForm):
    ip_address = TextField('IP address', default='0.0.0.0')
    port = IntegerField('Port', default=514)

def configure_form(cls):
    for property in ('source', 'content'):
        setattr(cls, property, TextField(property))
        setattr(cls, property + 'regex', BooleanField('Regex'))
    return cls

@configure_form
class LogFiltering(FlaskForm):
    pass
