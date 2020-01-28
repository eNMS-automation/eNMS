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
            sleep(0.2)
        else:
            for com in commands:
                self.shell.send(com)
                sleep(0.2)

    def receive_response(self, buff_size=1024):
        while self.shell.recv_ready():
            return self.shell.recv(buff_size)

    def is_shell_open(self):
        if self.shell.closed is True:
            return False
        else:
            return True


class Server(ServerInterface):

    def __init__(self, username=None):
        self.event = Event()
        self.username = username

    def check_channel_request(self, kind, *_):
        return OPEN_SUCCEEDED if kind == "session" else OPEN_FAILED

    def check_auth_password(self, username, password):
        return AUTH_FAILED

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
        self.chan = self.transport.accept(20)
        server.event.wait(10)

    def receive_data(self, client, channel):
        log = ""
        while client.is_shell_open():
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
        while client.is_shell_open():
            client.shell.send(channel.recv(512))

    def start(self, **kwargs):
        self.create_server()
        while not self.chan:
            time.sleep(0.5)
        username, password = self.username, self.password
        device = Client(
            kwargs["ip_address"], username, password, self.chan, port=kwargs["port"]
        )
        try:
            device.connect()
            device.invoke_shell()
        except paramiko.ssh_exception.AuthenticationException as e:
            device.close()
            self.transport.close()
            threading.Event().clear()
        except Exception as e:
            device.close()
            self.transport.close()
            threading.currentThread().exit(1)
        Thread(target=self.receive_data, args=(device, self.chan)).start()
        Thread(target=self.send_data, args=(device, self.chan)).start()
