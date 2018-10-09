from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

from eNMS.base.associations import job_workflow_table
from eNMS.base.models import CustomBase
from eNMS.services.models import Job


class WorkflowEdge(CustomBase):

    __tablename__ = 'WorkflowEdge'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(Boolean)
    source_id = Column(Integer, ForeignKey('Job.id'))
    source = relationship(
        'Job',
        primaryjoin='Job.id == WorkflowEdge.source_id',
        backref=backref('destinations', cascade='all, delete-orphan'),
        foreign_keys='WorkflowEdge.source_id'
    )
    destination_id = Column(Integer, ForeignKey('Job.id'))
    destination = relationship(
        'Job',
        primaryjoin='Job.id == WorkflowEdge.destination_id',
        backref=backref('sources', cascade='all, delete-orphan'),
        foreign_keys='WorkflowEdge.destination_id'
    )
    workflow_id = Column(Integer, ForeignKey('Workflow.id'))
    workflow = relationship(
        'Workflow',
        back_populates='edges',
        foreign_keys='WorkflowEdge.workflow_id'
    )

    @property
    def serialized(self):
        properties = self.properties
        properties['source'] = self.source.serialized
        properties['destination'] = self.destination.serialized
        return properties


class Workflow(Job):

    __tablename__ = 'Workflow'

    id = Column(Integer, ForeignKey('Job.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    jobs = relationship(
        'Job',
        secondary=job_workflow_table,
        back_populates='workflows'
    )
    edges = relationship('WorkflowEdge', back_populates='workflow')
    start_job = Column(Integer)
    end_job = Column(Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'workflow',
    }

    def run(self, workflow=None):
        runtime = str(datetime.now())
        start_job = retrieve(Task, id=self.job.start_job)
        if not start_job:
            return False, {runtime: 'No start task in the workflow.'}
        tasks, visited = [start_job], set()
        workflow_results = {}
        while tasks:
            task = tasks.pop()
            # We check that all predecessors of the task have been visited
            # to ensure that the task will receive the full payload.
            # If it isn't the case, we put it back in the heap and move on to
            # another task.
            if any(n not in visited for n in task.task_sources(self.job)):
                continue
            visited.add(task)
            task_results = task.run(workflow, workflow_results)
            success = task_results['success']
            if task.id == self.job.end_task:
                workflow_results['success'] = success
            for successor in task.task_successors(self.job, success):
                if successor not in visited:
                    tasks.append(successor)
            workflow_results[task.name] = task_results
            sleep(task.waiting_time)
        self.job.logs[runtime] = workflow_results
        db.session.commit()
        return workflow_results

    @property
    def serialized(self):
        properties = self.properties
        properties['scheduled_tasks'] = [
            obj.properties for obj in getattr(self, 'scheduled_tasks')
        ]
        properties['jobs'] = [
            obj.properties for obj in getattr(self, 'jobs')
        ]
        properties['edges'] = [edge.serialized for edge in self.edges]
        return properties
