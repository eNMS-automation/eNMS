from paramiko import client, SSHClient, WarningPolicy
from time import sleep
from threading import Event
from paramiko import (
    AUTH_FAILED,
    AUTH_SUCCESSFUL,
    RSAKey,
    OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED as OPEN_FAILED,
    OPEN_SUCCEEDED,
    ServerInterface,
)
import threading
import logging
import os
import time
import datetime
import socket
import sys
import traceback
from random import choice
import string
import paramiko
from re import sub
from threading import Thread, currentThread


class Client(SSHClient):
    def __init__(self, hostname, username, password):
        super().__init__()
        self.load_system_host_keys()
        self.set_missing_host_key_policy(WarningPolicy)
        self.connect(
            hostname=hostname, username=username, password=password,
        )
        self.shell = self.invoke_shell()

    def receive_response(self):
        while self.shell.recv_ready():
            return self.shell.recv(1024)


class Server(ServerInterface):
    def __init__(self, username=None):
        self.event = Event()
        self.username = username

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
        self,
        hostname,
        username,
        password,
        calling_user=None,
        logpath="./logs/handoffssh_logs/",
    ):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.calling_user = calling_user
        all_chars = string.ascii_letters + string.digits
        self.sshlogin = (
            self.calling_user + "___" + "".join(choice(all_chars) for i in range(32))
        )
        self.calling_password = "".join(choice(all_chars) for i in range(32))
        logstring = "".join(choice(all_chars) for i in range(6))
        if not os.path.exists(logpath):
            os.makedirs(logpath)
        self.sessionLogger = logging.getLogger(logstring)
        fh = logging.FileHandler(
            filename=f'{logpath}/{hostname}-{datetime.datetime.now().strftime("%m%d%y_%H%M%S")}.log'
        )
        self.sessionLogger.addHandler(fh)
        try:
            self.host_key = paramiko.RSAKey.from_private_key_file("rsa.key")
        except FileNotFoundError:
            genkey = paramiko.RSAKey.generate(2048)
            genkey.write_private_key_file("rsa.key")
        self.port = choice(range(50000, 50999))

    def create_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self.port))
        sock.listen(100)
        sock.settimeout(30)
        self.transport = paramiko.Transport(sock.accept()[0])
        self.transport.add_server_key(self.host_key)
        server = Server(self.sshlogin)
        self.transport.start_server(server=server)
        self.channel = self.transport.accept(20)
        server.event.wait(10)

    def receive_data(self, client, channel):
        log = ""
        while not client.shell.closed:
            response = client.receive_response()
            if not response:
                continue
            channel.send(response)
            log += response.decode("utf-8", "replace")
            if "\n" in log:
                self.sessionLogger.info("\n".join(l for l in log.splitlines() if l))
                log = ""
            time.sleep(0.001)

    def send_data(self, client, channel):
        while not client.shell.closed:
            client.shell.send(channel.recv(512))

    def start(self, **kwargs):
        self.create_server()
        while not self.channel:
            time.sleep(0.5)
        username, password = self.username, self.password
        device = Client(kwargs["ip_address"], username, password)
        Thread(target=self.receive_data, args=(device, self.channel)).start()
        Thread(target=self.send_data, args=(device, self.channel)).start()
