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
        self.config["SECRET_KEY"] = getenv("TERMINAL_SECRET_KEY", "secret_key")
        self.socketio = SocketIO(
            self, cors_allowed_origins=getenv("CORS_ALLOWED_ORIGINS")
        )
        self.configure_routes()

    def send_data(self):
        while True:
            try:
                self.socketio.sleep(0.1)
                output = read(self.file_descriptor, 1024).decode()
                self.socketio.emit("output", output, namespace="/terminal")
            except OSError:
                break

    def configure_routes(self):
        @self.route(f"/{getenv('ENDPOINT')}")
        def index():
            redirection = getenv("REDIRECTION") == "True"
            return render_template("index.html", redirection=redirection)

        @self.route("/shutdown", methods=["POST"])
        def shutdown():
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

        @self.socketio.on("input", namespace="/terminal")
        def input(data):
            write(self.file_descriptor, data.encode())

        @self.socketio.on("connect", namespace="/terminal")
        def connect():
            self.process_id, self.file_descriptor = fork()
            if self.process_id:
                self.socketio.start_background_task(target=self.send_data)
            else:
                port = f"-p {getenv('PORT')}"
                if getenv("PROTOCOL") == "telnet":
                    command = f"telnet {getenv('IP_ADDRESS')}"
                elif getenv("PASSWORD"):
                    command = (
                        f"sshpass -p {getenv('PASSWORD')} ssh {getenv('OPTIONS')} "
                        f"{getenv('USERNAME')}@{getenv('IP_ADDRESS')} {port}"
                    )
                else:
                    command = f"ssh {getenv('OPTIONS')} {getenv('IP_ADDRESS')} {port}"
                run(command.split())


app = Server()
