from sqlalchemy import Column, Integer, String
from base.models import CustomBase

class Task(CustomBase):
    
    __tablename__ = 'Task'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)
    creation_time = Column(Integer)
    
    # scheduling parameters
    frequency = Column(String(120))
    scheduled_date = Column(String)
    
    # script parameters
    script = Column(String)
    creator = Column(String)
    
    def __init__(self, script, **data):
        self.name = data['name']
        self.frequency = data['frequency']
        self.scheduled_date = self.datetime_conversion(str(data['scheduled_date']))
        self.creation_time = str(datetime.now())
        self.creator = data['user']
        self.script = script
        # by default, a task is active but it can be deactivated
        self.is_active = True
        
    def datetime_conversion(self, scheduled_date):
        dt = datetime.datetime.strptime(scheduled_date, '%d/%m/%Y %H:%M:%S')
        return datetime.datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')
                
    def pause_task(self):
        scheduler.pause_job(self.name)
        self.status = 'Suspended'
        
    def resume_task(self):
        scheduler.resume_job(self.name)
        self.status = "Active"
        
    def __repr__(self):
        return str(self.name)
