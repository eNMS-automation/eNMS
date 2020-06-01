from sqlalchemy import Boolean, ForeignKey, Integer

from eNMS.database import db
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import (
    BooleanField,
    HiddenField,
    StringField,
)
from eNMS.models.automation import Service


class GitService(Service):

    __tablename__ = "git_service"
    pretty_name = "Git Action"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    git_repository = db.Column(db.SmallString)
    pull = db.Column(Boolean)
    commit = db.Column(Boolean)
    commit_message = db.Column(db.LargeString)
    psh = db.Column(Boolean)

    __mapper_args__ = {"polymorphic_identity": "git_service"}

    def job(self, run, payload, device=None):
        return {}


class GitForm(ServiceForm):
    form_type = HiddenField(default="git_service")
    repository = StringField("Remote Git Repository")
    pull = BooleanField("Git Pull")
    commit = BooleanField("Do 'git add' and commit")
    commit_message = StringField("Commit Message")
    push = BooleanField("Git Push")
