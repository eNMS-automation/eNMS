from git import Repo
from git.exc import GitCommandError
from pathlib import Path

repo = Repo(str(Path.cwd() / "configurations"))
try:
    repo.git.add(A=True)
    repo.git.commit(m="commit all")
except GitCommandError:
    pass
repo.remotes.origin.push()
