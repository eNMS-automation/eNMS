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
import random
import string
import paramiko


class SshConnection:
    def __init__(
        self,
        hostname,
        port,
        username,
        password,
        calling_user=None,
        listeningport=None,
        logpath="./logs/handoffssh_logs/",
        loglevel="info",
    ):
        # setup basic parameters
        self.hostname = hostname
        self.username = username
        self.password = password
        self.chan = None
        self.calling_user = calling_user
        all_chars = string.ascii_letters + string.digits
        self.sshlogin = (
            self.calling_user
            + "___"
            + "".join(random.choice(all_chars) for i in range(32))
        )
        self.calling_password = "".join(random.choice(all_chars) for i in range(32))
        # setup logging

        logstring = "".join(random.choice(all_chars) for i in range(6))
        self.loglevel = loglevel
        self.logpath = logpath
        if not os.path.exists(self.logpath):
            os.makedirs(self.logpath)
        self.sessionLogger = logging.getLogger(logstring)
        logging.getLogger(logstring).setLevel(logging.INFO)
        fmt = logging.Formatter("%(message)s")
        fh = logging.FileHandler(
            filename=f'{self.logpath}/{hostname}\
                -{datetime.datetime.now().strftime("%m%d%y_%H%M%S")}.log'
        )
        fh.terminator = ""
        fh.setFormatter(fmt)
        self.sessionLogger.addHandler(fh)

        try:
            self.host_key = paramiko.RSAKey.from_private_key_file("rsa.key")
        except FileNotFoundError:
            self.sessionLogger.info(
                "Error - RSA Key file does not exist.  Generating..."
            )
            genkey = paramiko.RSAKey.generate(2048)
            genkey.write_private_key_file("rsa.key")
        if listeningport is None:
            self.listeningport = random.choice(range(50000, 50999))
        else:
            self.listeningport = int(listeningport)

    def create_server(self):
        # now connect
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", self.listeningport))
        except Exception as e:
            self.sessionLogger.info("*** Bind failed: " + str(e) + "\n")
            traceback.print_exc()
            sys.exit(1)

        try:
            sock.listen(100)
            sock.settimeout(30)
            client, addr = sock.accept()
        except Exception as e:
            self.sessionLogger.info("*** Listen/accept failed: " + str(e) + "\n")
            traceback.print_exc()
            sys.exit(1)

        self.sessionLogger.info(f"Got a connection from {addr[0]}!\n")

        try:
            t = paramiko.Transport(client)
            self.transport = t
            t.set_gss_host(socket.getfqdn(""))
            try:
                t.load_server_moduli()
            except Exception:
                self.sessionLogger.info(
                    "(Failed to load moduli -- gex will be unsupported.)\n'"
                )
                raise
            t.add_server_key(self.host_key)
            server = Server(self.sshlogin)
            try:
                t.start_server(server=server)
            except paramiko.SSHException:
                self.sessionLogger.info("*** SSH negotiation failed.\n")
                sys.exit(1)

            # wait for auth
            self.chan = t.accept(20)
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
                t.close()
            except Exception:
                pass
            sys.exit(1)

    def recv_data(self, client, svr_chan):
        log = ""
        replace_chars = ["\r\n", "\n\r"]
        while client.is_shell_open():
            recv = client.receive_response()
            if recv is None:
                pass
            else:
                svr_chan.send(recv)
                log += recv.decode("utf-8", "replace")
                if "\n" in log:
                    # remove double new-line interpretation
                    # by '\r\n' or '\n\r' in the logger.
                    for char in replace_chars:
                        if char in log:
                            log = log.replace(char, "\n")
                    # remove whitespace chars from being printed in the logger.
                    self.sessionLogger.info(log)
                    log = ""
                time.sleep(0.001)
        client._client.get_transport().close()

    def send_data(self, client, svr_chan):
        while client.is_shell_open():
            com = svr_chan.recv(512)
            if client.is_shell_open():
                client.shell.send(com)
            else:
                svr_chan.close()

    def start(self, device):
        """
        Starts the server session and then
        connects to the device when a connection is received.
        """
        self.create_server()
        while self.chan is None:
            time.sleep(0.5)

        username, password = self.username, self.password

        sshdevice = SshClient(
            device.ip_address, username, password, self.chan, port=device.port
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
                {device.ip_address}.  Error: {e}\n"
            )
            sshdevice.close()
            self.transport.close()
            threading.currentThread().exit(1)

        tc = threading.Thread(target=self.recv_data, args=(sshdevice, self.chan))
        tc.start()

        ts = threading.Thread(target=self.send_data, args=(sshdevice, self.chan))
        ts.start()
