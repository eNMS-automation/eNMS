from flask_wtf import FlaskForm
from wtforms import *

class SyslogServerForm(FlaskForm):
    ip_address = TextField('IP address', default='0.0.0.0')
    port = IntegerField('Port', default=514)

