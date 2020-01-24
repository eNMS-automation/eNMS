

import base64
import threading

import paramiko
from paramiko import AUTH_FAILED, AUTH_SUCCESSFUL, RSAKey, OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED, OPEN_SUCCEEDED, ServerInterface
from paramiko.py3compat import decodebytes


class Server(ServerInterface):

    try:
        key = RSAKey.from_private_key_file("rsa.key")
    except FileNotFoundError:
        genkey = RSAKey.generate(2048)
        genkey.write_private_key_file("rsa.key")
        key = RSAKey.from_private_key_file("rsa.key")
    data = base64.b64encode(key.asbytes())

    good_pub_key = RSAKey(data=decodebytes(data))

    def __init__(self, username=None):
        self.event = threading.Event()
        self.username = username

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return OPEN_SUCCEEDED
        return OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        return AUTH_FAILED

    def check_auth_none(self, username):
        return AUTH_SUCCESSFUL if username == self.username else AUTH_FAILED

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(
        self, channel, term, width, height, pixelwidth, pixelheight, modes
    ):
        return True
