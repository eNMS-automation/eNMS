from datetime import datetime
from time import sleep
from paramiko import (
    AUTH_FAILED,
    AUTH_SUCCESSFUL,
    client,
    RSAKey,
    OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED as OPEN_FAILED,
    OPEN_SUCCEEDED,
    ServerInterface,
    SSHClient,
    Transport,
    WarningPolicy,
)
from random import choice
from socket import AF_INET, socket, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import currentThread, Event, Thread

import logging
import os
import sys


class Client(SSHClient):
    def __init__(self, connection):
        super().__init__()
        self.load_system_host_keys()
        self.set_missing_host_key_policy(WarningPolicy)
        self.connect(
            hostname=connection.hostname,
            username=connection.username,
            password=connection.password,
        )
        self.shell = self.invoke_shell()


class Server(ServerInterface):
    def __init__(self, connection):
        self.event = Event()
        self.username = connection.login
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(("", connection.port))
        sock.listen(100)
        sock.settimeout(30)
        self.transport = Transport(sock.accept()[0])
        self.transport.add_server_key(connection.host_key)
        self.transport.start_server(server=self)
        self.channel = self.transport.accept(10)

    def check_channel_request(self, kind, *_):
        return OPEN_SUCCEEDED if kind == "session" else OPEN_FAILED

    def check_auth_none(self, username):
        return AUTH_SUCCESSFUL if username == self.username else AUTH_FAILED

    def check_channel_shell_request(self, *_):
        self.event.set()
        return True

    def check_channel_pty_request(self, *_):
        return True


class SshConnection:
    def __init__(
        self, hostname, username, password, login,
    ):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.login = login
        logpath = "./logs/handoffssh_logs"
        if not os.path.exists(logpath):
            os.makedirs(logpath)
        self.sessionLogger = logging.getLogger(login)
        fh = logging.FileHandler(
            filename=f'{logpath}/{hostname}-{datetime.now().strftime("%m%d%y_%H%M%S")}.log'
        )
        self.sessionLogger.addHandler(fh)
        try:
            self.host_key = RSAKey.from_private_key_file("rsa.key")
        except FileNotFoundError:
            self.host_key = RSAKey.generate(2048)
            self.host_key.write_private_key_file("rsa.key")
        self.port = choice(range(50000, 50999))

    def receive_data(self, shell, channel):
        log = ""
        while not shell.closed:
            response = shell.recv(1024)
            if not response:
                continue
            channel.send(response)
            log += response.decode("utf-8", "replace")
            if "\n" in log:
                self.sessionLogger.info("\n".join(l for l in log.splitlines() if l))
                log = ""
            sleep(0.001)

    def send_data(self, shell, channel):
        while not shell.closed:
            shell.send(channel.recv(512))

    def start(self):
        args = (Client(self).shell, Server(self).channel)
        Thread(target=self.receive_data, args=args).start()
        Thread(target=self.send_data, args=args).start()
