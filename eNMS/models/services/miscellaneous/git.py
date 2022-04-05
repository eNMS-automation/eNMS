from git import Repo
from pathlib import Path
from sqlalchemy import Boolean, ForeignKey, Integer

from eNMS.database import db
from eNMS.forms import ServiceForm
from eNMS.fields import BooleanField, HiddenField, SelectMultipleField, StringField
from eNMS.models.automation import Service


class GitService(Service):

    __tablename__ = "git_service"
    pretty_name = "Git Action"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    actions = db.Column(db.List)
    local_repository = db.Column(db.SmallString)
    relative_path = db.Column(Boolean, default=False)
    remote_repository = db.Column(db.SmallString)
    commit_message = db.Column(db.LargeString)

    __mapper_args__ = {"polymorphic_identity": "git_service"}

    def job(self, run, device=None):
        local_path = run.sub(run.local_repository, locals())
        if self.actions & {"clone", "shallow_clone"}:
            remote_path, kwargs = run.sub(run.remote_repository, locals()), {}
            if "shallow_clone" in self.actions:
                kwargs.udpate({"filter": "{tree:0,blob:none}", "sparse": True})
            repo = Repo.clone_from(remote_path, local_path, **kwargs)
        else:
            repo = Repo(Path.cwd() / local_path if self.relative_path else local_path)
        if "add_commit" in self.actions:
            repo.git.add(A=True)
            repo.git.commit(m=self.commit_message)
        if "pull" in self.actions:
            repo.remotes.origin.pull()
        if "push" in self.actions:
            repo.remotes.origin.push()
        return {"success": True}


class GitForm(ServiceForm):
    form_type = HiddenField(default="git_service")
    actions = SelectMultipleField(
        choices=(
            ("clone", "Clone"),
            ("shallow_clone", "Shallow Clone"),
            ("add_commit", "Do 'git add' and commit"),
            ("pull", "Pull"),
            ("push", "Push"),
        )
    )
    local_repository = StringField("Path to Local Git Repository")
    relative_path = BooleanField("Path is relative to eNMS folder")
    remote_repository = StringField("Path to Remote Git Repository")
    commit_message = StringField("Commit Message")
