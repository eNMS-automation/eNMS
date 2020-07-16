from git import Repo
from pathlib import Path
from sqlalchemy import Boolean, ForeignKey, Integer

from eNMS.database import db
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import BooleanField, HiddenField, StringField
from eNMS.models.automation import Service


class GitService(Service):

    __tablename__ = "git_service"
    pretty_name = "Git Action"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    git_repository = db.Column(db.SmallString)
    relative_path = db.Column(Boolean)
    pull = db.Column(Boolean)
    add_commit = db.Column(Boolean)
    commit_message = db.Column(db.LargeString)
    push = db.Column(Boolean)

    __mapper_args__ = {"polymorphic_identity": "git_service"}

    def job(self, run, payload, device=None):
        repo = Repo(
            Path.cwd() / self.git_repository
            if self.relative_path
            else self.git_repository
        )
        if self.pull:
            repo.remotes.origin.pull()
        if self.add_commit:
            repo.git.add(A=True)
            repo.git.commit(m=self.commit_message)
        if self.push:
            repo.remotes.origin.push()
        return {"success": True}


class GitForm(ServiceForm):
    form_type = HiddenField(default="git_service")
    git_repository = StringField("Path to Local Git Repository")
    relative_path = BooleanField("Path is relative to eNMS folder")
    pull = BooleanField("Git Pull")
    add_commit = BooleanField("Do 'git add' and commit")
    commit_message = StringField("Commit Message")
    push = BooleanField("Git Push")
