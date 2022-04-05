from git import Repo
from pathlib import Path
from sqlalchemy import Boolean, ForeignKey, Integer

from eNMS.database import db
from eNMS.forms import ServiceForm
from eNMS.fields import BooleanField, HiddenField, SelectField, StringField
from eNMS.models.automation import Service


class GitService(Service):

    __tablename__ = "git_service"
    pretty_name = "Git Action"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    action = db.Column(db.SmallString, default="none")
    git_repository = db.Column(db.SmallString)
    relative_path = db.Column(Boolean, default=False)
    remote_repository = db.Column(db.SmallString)
    add_commit = db.Column(Boolean, default=False)
    commit_message = db.Column(db.LargeString)
    push = db.Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "git_service"}

    def job(self, run, device=None):
        local_path = run.sub(run.git_repository, locals())
        if self.action in ("clone", "shallow_clone"):
            remote_path, kwargs = run.sub(run.remote_repository, locals()), {}
            if self.action == "shallow_clone":
                kwargs.udpate({"filter": "{tree:0,blob:none}", "sparse": True})
            repo = Repo.clone_from(remote_path, local_path, **kwargs)
        else:
            repo = Repo(Path.cwd() / local_path if self.relative_path else local_path)
        if self.add_commit:
            repo.git.add(A=True)
            repo.git.commit(m=self.commit_message)
        if self.pull:
            repo.remotes.origin.pull()
        if self.push:
            repo.remotes.origin.push()
        return {"success": True}


class GitForm(ServiceForm):
    form_type = HiddenField(default="git_service")
    action = SelectField(
        choices=(
            ("none", "None"),
            ("pull", "Pull"),
            ("clone", "Clone"),
            ("shallow_clone", "Shallow Clone"),
        )
    )
    git_repository = StringField("Path to Local Git Repository")
    relative_path = BooleanField("Path is relative to eNMS folder")
    remote_repository = StringField("Path to Remote Git Repository")
    add_commit = BooleanField("Do 'git add' and commit")
    commit_message = StringField("Commit Message")
    push = BooleanField("Git Push")
