from paramiko import client, SSHClient, WarningPolicy
import time


class SshClient(SSHClient):
    def __init__(self, hostname, username, password, channel, port=22, timeout=5):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.channel = channel
        self._client = client.SSHClient()
        self._client.load_system_host_keys()
        self._client.set_missing_host_key_policy(WarningPolicy)

    def connect(self):
        self._client.connect(
            hostname=self.hostname,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=5,
        )

    def close(self):
        self._client.get_transport().close()

    def invoke_shell(self):
        self.shell = self._client.invoke_shell()

    def send_command(self, commands):
        if isinstance(commands, str):
            self.shell.send(commands)
            time.sleep(0.2)
        else:
            for com in commands:
                self.shell.send(com)
                time.sleep(0.2)

    def receive_response(self, buff_size=1024):
        while self.shell.recv_ready():
            return self.shell.recv(buff_size)

    def is_shell_open(self):
        if self.shell.closed is True:
            return False
        else:
            return True
