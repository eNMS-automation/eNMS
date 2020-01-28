from eNMS.handoffssh.client import SshClient
from eNMS.handoffssh.server import Server
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


class SshConnection:
    def __init__(
        self,
        hostname,
        username,
        password,
        calling_user=None,
        logpath="./logs/handoffssh_logs/",
    ):
        # setup basic parameters
        self.hostname = hostname
        self.username = username
        self.password = password
        self.chan = None
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
        logging.getLogger(logstring).setLevel(logging.INFO)
        fmt = logging.Formatter("%(message)s")
        fh = logging.FileHandler(
            filename=f'{logpath}/{hostname}\
                -{datetime.datetime.now().strftime("%m%d%y_%H%M%S")}.log'
        )
        fh.terminator = ""
        fh.setFormatter(fmt)
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
        client, addr = sock.accept()
        self.sessionLogger.info(f"Got a connection from {addr[0]}!\n")
        try:
            self.transport = paramiko.Transport(client)
            self.transport.set_gss_host(socket.getfqdn(""))
            self.transport.add_server_key(self.host_key)
            server = Server(self.sshlogin)
            try:
                self.transport.start_server(server=server)
            except paramiko.SSHException:
                self.sessionLogger.info("*** SSH negotiation failed.\n")
                sys.exit(1)
            self.chan = self.transport.accept(20)
            if self.chan is None:
                self.sessionLogger.info("*** No channel.\n")
                sys.exit(1)
            self.sessionLogger.info("Authenticated!\n")
            server.event.wait(10)
            if not server.event.is_set():
                self.sessionLogger.info("*** Client never asked for a shell.\n")
                sys.exit(1)
            self.chan.send(f"\r\n\r\nConnecting you to {self.hostname}...\r\n\r\n")

        except Exception as e:
            self.sessionLogger.info(
                "*** Caught exception: " + str(e.__class__) + ": " + str(e) + "\n"
            )
            traceback.print_exc()
            try:
                self.transport.close()
            except Exception:
                pass
            sys.exit(1)

    def recv_data(self, client, channel):
        while client.is_shell_open():
            response = client.receive_response()
            if not response:
                continue
            channel.send(response)
            self.sessionLogger.info(response.decode("utf-8", "replace"))
            time.sleep(0.001)
        client._client.get_transport().close()

    def send_data(self, client, channel):
        while client.is_shell_open():
            com = channel.recv(512)
            if client.is_shell_open():
                client.shell.send(com)
            else:
                channel.close()

    def start(self, **device):
        self.create_server()
        while self.chan is None:
            time.sleep(0.5)
        username, password = self.username, self.password
        sshdevice = SshClient(
            device["ip_address"], username, password, self.chan, port=device["port"]
        )
        try:
            sshdevice.connect()
            sshdevice.invoke_shell()
        except paramiko.ssh_exception.AuthenticationException as e:
            self.sessionLogger.info(f"{e}\n")
            sshdevice.close()
            self.chan.send(f"{e}")
            self.transport.close()
            threading.Event().clear()
        except Exception as e:
            self.sessionLogger.info(
                f"There was an error attempting to connect to \
                {device['ip_address']}.  Error: {e}\n"
            )
            sshdevice.close()
            self.transport.close()
            threading.currentThread().exit(1)
        tc = threading.Thread(target=self.recv_data, args=(sshdevice, self.chan))
        tc.start()
        ts = threading.Thread(target=self.send_data, args=(sshdevice, self.chan))
        ts.start()
