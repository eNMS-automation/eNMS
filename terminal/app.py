from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO
from logging import ERROR, getLogger
from os import getenv, read, write
from pty import fork
from requests import post
from requests.auth import HTTPBasicAuth
from subprocess import run
from uuid import uuid4


class Server(Flask):
    def __init__(self):
        super().__init__(__name__)
        getLogger("werkzeug").setLevel(ERROR)
        self.configure_routes()

    def configure_routes(self):
        @self.route("/shutdown", methods=["POST"])
        def shutdown():
            request.environ.get("werkzeug.server.shutdown")()
            post(
                f"{getenv('APP_ADDRESS')}/rest/instance/session",
                json={
                    "content": request.json,
                    "device_id": getenv("DEVICE"),
                    "name": str(uuid4()),
                    "timestamp": str(datetime.now()),
                    "user": getenv("USER"),
                },
                auth=HTTPBasicAuth(getenv("ENMS_USER"), getenv("ENMS_PASSWORD")),
                verify=False if getenv("VERIFY_CERTIFICATE", True) == "False" else True,
            )
            return jsonify(True)


app = Server()
