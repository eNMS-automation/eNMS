from git import Git, Repo
from git.exc import GitCommandError
from pathlib import Path

a = Path.cwd() / 'configurations'

key = '''ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC8maXHDzY2YWFArhpKAnnNQ9hOH6+CVYEjfXF9QApZT0gd60RK8Pnp0ZZeEI/PP9FOURQ+UI8XItHDkAxqh1n8IKciGZj3ggFuiLpULLVEXJkMy6UwNXjw5d9Y1o3KsDmzNH2ulRn64xPjtgRnEGDVOeOO94nN0GS/US2VyHp8b4WqZ8/KYTDz8uhakNfiwJF9edwType9uuz/M239/ceu8GoNKRjsN9r7dIkB6YPIZ+48/KyOiL2Zw90WZ42S0IgAS8+poBPU7hHIJZ/LXe0K/znGfl68Qfc+Ogo8iZjvGL6ZLdFYIS12RIuxed9/qMffo1HRFUS2dw3QeC78qjBeewixxtI6sIyfyioUC6P57WuOKNgHNhfKJR+/AHRwBU3RrNUt9x6WAvnHi98sizNUTDxOKeFEjslnnSPT3K3ayFLDZqYkNLzS1tAq/JafKI8q2fMbn+dXm257AErHmdjW5kCnZygl3oh80QBsWW2VDqUkSZeTSDKCbP0Zk0XABaEaKH/8i4dVLBdQ+fJaV4ZBWtVUq89Kxzzh7aAiYB6uZ/SyZxOMiWh6PD77g3HsnLnAK/LjSkXDlGNvhKfBfkAe8s9itfxLZOvcjn4tu3Z68ZsrJIyFjJgAokuUVn1wKemOk5cuquTWq3fXzB3z7NmvSmUwWIP7Sdke/FQxAbNGXQ== antoine.fourmy@gmail.com'''


with Git().custom_environment(GIT_SSH_COMMAND=f'ssh -i {key}'):
    repo = Repo(str(a))
    try:
        repo.git.add(A=True)
        repo.git.commit(m='commit all')
    except GitCommandError:
        pass
    repo.remotes.origin.push()