from app import db
from models import *

def show_devices():
    with db.app.app_context():
        print(Device.query.all())