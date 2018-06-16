from apscheduler.jobstores.base import JobLookupError
from copy import deepcopy
from datetime import datetime, timedelta
from multiprocessing.pool import ThreadPool
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, PickleType
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship


from eNMS import db, scheduler
from eNMS.base.helpers import get_obj
from eNMS.base.models import (
    inner_task_node_table,
    scheduled_task_node_table,
    inner_task_script_table,
    scheduled_task_script_table,
    CustomBase
)
from eNMS.base.properties import cls_to_properties


def script_job(task_name):
    with scheduler.app.app_context():
        job_time = str(datetime.now())
        task = get_obj(Task, name=task_name)
        logs = deepcopy(task.logs)
        logs[job_time] = {}
        nodes = task.nodes if task.nodes else ['dummy']
        for script in task.scripts:
            results = {}
            pool = ThreadPool(processes=len(nodes))
            args = [(task, node, results) for node in nodes]
            pool.map(script.job, args)
            pool.close()
            pool.join()
            logs[job_time][script.name] = results
        result = True
        for script in task.scripts:
            for node in task.nodes:
                if not logs[job_time][script.name][node.name]:
                    result = False
        task.result = result
        task.logs = logs
        db.session.commit()


def workflow_job(task_name):
    with scheduler.app.app_context():
        task = get_obj(Task, name=task_name)
        task.result = task.scheduled_workflow.run()
        task.logs = {'result': 'go to the workflow editor to see the result'}
        db.session.commit()


class Task(CustomBase):

    __tablename__ = 'Task'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    status = Column(String)
    result = Column(Boolean)
    type = Column(String)
    user_id = Column(Integer, ForeignKey('User.id'))
    user = relationship('User', back_populates='tasks')
    logs = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {
        'polymorphic_identity': 'Task',
        'polymorphic_on': type
    }

    def __init__(self, **data):
        self.status = 'active'
        self.name = data['name']
        self.user = data['user']


class ScheduledTask(Task):

    __tablename__ = 'ScheduledTask'

    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    recurrent = Column(Boolean, default=False)
    creation_time = Column(Integer)
    frequency = Column(String(120))
    start_date = Column(String)
    end_date = Column(String)
    creator = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'ScheduledTask',
    }

    def __init__(self, **data):
        self.frequency = data['frequency']
        self.recurrent = bool(self.frequency)
        self.creation_time = str(datetime.now())
        self.creator = data['user'].name
        # if the start date is left empty, we turn the empty string into
        # None as this is what AP Scheduler is expecting
        for date in ('start_date', 'end_date'):
            js_date = data[date]
            value = self.datetime_conversion(js_date) if js_date else None
            setattr(self, date, value)
        self.is_active = True
        super(ScheduledTask, self).__init__(**data)
        self.schedule()

    def schedule(self):
        if self.frequency:
            self.recurrent = True
            self.recurrent_scheduling()
        else:
            self.one_time_scheduling()

    def datetime_conversion(self, date):
        dt = datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
        return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')

    def pause_task(self):
        scheduler.pause_job(self.creation_time)
        self.status = 'suspended'
        db.session.commit()

    def resume_task(self):
        scheduler.resume_job(self.creation_time)
        self.status = 'active'
        db.session.commit()

    def delete_task(self):
        try:
            scheduler.delete_job(self.creation_time)
        except JobLookupError:
            pass
        db.session.commit()

    def recurrent_scheduling(self):
        if not self.start_date:
            self.start_date = datetime.now() + timedelta(seconds=15)
        # run the job on a regular basis with an interval trigger
        scheduler.add_job(
            id=self.creation_time,
            func=self.job,
            args=[self.name],
            trigger='interval',
            start_date=self.start_date,
            end_date=self.end_date,
            seconds=int(self.frequency),
            replace_existing=True
        )

    def one_time_scheduling(self):
        if not self.start_date:
            # when the job is scheduled to run immediately, it may happen that
            # the job is run even before the task is created, in which case
            # it fails because it cannot be retrieve from the Task column of
            # the database: we introduce a delta of 5 seconds.
            # other situation: the server is too slow and the job cannot be
            # run at all, eg 'job was missed by 0:00:09.465684'
            self.start_date = datetime.now() + timedelta(seconds=5)
        # execute the job immediately with a date-type job
        # when date is used as a trigger and run_date is left undetermined,
        # the job is executed immediately.
        scheduler.add_job(
            id=self.creation_time,
            run_date=self.start_date,
            func=self.job,
            args=[self.name],
            trigger='date'
        )


class ScheduledScriptTask(ScheduledTask):

    __tablename__ = 'ScheduledScriptTask'

    id = Column(Integer, ForeignKey('ScheduledTask.id'), primary_key=True)
    scripts = relationship(
        'Script',
        secondary=scheduled_task_script_table,
        back_populates='tasks'
    )
    nodes = relationship(
        'Node',
        secondary=scheduled_task_node_table,
        back_populates='scheduled_tasks'
    )

    __mapper_args__ = {
        'polymorphic_identity': 'ScheduledScriptTask',
    }

    def __init__(self, **data):
        self.scripts = data['scripts']
        self.nodes = data['nodes']
        self.job = script_job
        super(ScheduledScriptTask, self).__init__(**data)

    def run(self):
        job_time = str(datetime.now())
        logs = deepcopy(self.logs)
        logs[job_time] = {}
        nodes = self.nodes if self.nodes else ['dummy']
        for script in self.scripts:
            results = {}
            pool = ThreadPool(processes=len(nodes))
            args = [(self, node, results) for node in nodes]
            pool.map(script.job, args)
            pool.close()
            pool.join()
            logs[job_time][script.name] = results
        result = True
        for script in self.scripts:
            for node in self.nodes:
                if not logs[job_time][script.name][node.name]:
                    result = False
        self.result = result
        self.logs = logs
        db.session.commit()
        return result

    @property
    def properties(self):
        return {p: str(getattr(self, p)) for p in cls_to_properties['ScheduledTask']}

    @property
    def serialized(self):
        properties = self.properties
        for prop in ('scripts', 'nodes'):
            properties[prop] = [obj.properties for obj in getattr(self, prop)]
        return properties


class ScheduledWorkflowTask(ScheduledTask):

    __tablename__ = 'ScheduledWorkflowTask'

    id = Column(Integer, ForeignKey('ScheduledTask.id'), primary_key=True)
    scheduled_workflow_id = Column(Integer, ForeignKey('Workflow.id'))
    scheduled_workflow = relationship('Workflow', back_populates='tasks')

    __mapper_args__ = {
        'polymorphic_identity': 'ScheduledWorkflowTask',
    }

    def __init__(self, **data):
        self.scheduled_workflow = data['workflow']
        self.job = workflow_job
        super(ScheduledWorkflowTask, self).__init__(**data)

    def run():
        self.result = task.scheduled_workflow.run()
        self.logs = {'result': 'go to the workflow editor to see the result'}
        db.session.commit()
        return result

    @property
    def properties(self):
        return {p: str(getattr(self, p)) for p in cls_to_properties['ScheduledTask']}

    @property
    def serialized(self):
        properties = {p: str(getattr(self, p)) for p in cls_to_properties['ScheduledTask']}
        # properties['scheduled_workflow'] = self.scheduled_workflow.properties
        return properties


class InnerTask(Task):

    __tablename__ = 'InnerTask'

    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    waiting_time = Column(Integer)
    scripts = relationship(
        'Script',
        secondary=inner_task_script_table,
        back_populates='inner_tasks'
    )
    nodes = relationship(
        'Node',
        secondary=inner_task_node_table,
        back_populates='inner_tasks'
    )
    workflow_id = Column(Integer, ForeignKey('Workflow.id'))
    parent_workflow = relationship('Workflow', back_populates='inner_tasks')
    x = Column(Integer, default=0.)
    y = Column(Integer, default=0.)


    __mapper_args__ = {
        'polymorphic_identity': 'InnerTask',
    }

    def __init__(self, **data):
        self.waiting_time = 0.
        self.nodes = data['nodes']
        self.scripts = data['scripts']
        self.parent_workflow = data['workflow']
        self.is_active = True
        super(InnerTask, self).__init__(**data)

    def run(self):
        job_time = str(datetime.now())
        logs = deepcopy(self.logs)
        logs[job_time] = {}
        nodes = self.nodes if self.nodes else ['dummy']
        for script in self.scripts:
            results = {}
            pool = ThreadPool(processes=len(nodes))
            args = [(self, node, results) for node in nodes]
            pool.map(script.job, args)
            pool.close()
            pool.join()
            logs[job_time][script.name] = results
        result = True
        for script in self.scripts:
            for node in self.nodes:
                if not logs[job_time][script.name][node.name]:
                    result = False
        self.result = result
        self.logs = logs
        db.session.commit()
        return result

    @property
    def properties(self):
        return {p: str(getattr(self, p)) for p in cls_to_properties['InnerTask']}

    @property
    def serialized(self):
        properties = self.properties
        for prop in ('scripts', 'nodes'):
            properties[prop] = [obj.properties for obj in getattr(self, prop)]
        # properties['parent_workflow'] = self.parent_workflow.properties
        return properties

    def task_neighbors(self, type):
        return [x.destination for x in self.destinations if x.type == type]


task_types = {
    'script_task': ScheduledScriptTask,
    'workflow_task': ScheduledWorkflowTask,
    'inner_task': InnerTask
}


def task_factory(task_type, **kwargs):
    cls = task_types[task_type]
    task = get_obj(cls, name=kwargs['name'])
    if task:
        for property, value in kwargs.items():
            if property in ('start_date', 'end_date') and value:
                value = task.datetime_conversion(value)
            setattr(task, property, value)
    else:
        task = cls(**kwargs)
        db.session.add(task)
    db.session.commit()
    return task
