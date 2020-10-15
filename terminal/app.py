from flask import Flask, render_template
from flask_socketio import SocketIO
from os import getenv, kill, read, write
from pty import fork
from signal import SIGKILL
from subprocess import run


class Server(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.config["SECRET_KEY"] = "secret"
        self.socketio = SocketIO(self)
        self.configure_routes()

    def send_data(self):
        while True:
            self.socketio.sleep(0.1)
            try:
                output = read(self.file_descriptor, 1024).decode()
            except OSError:
                break
            self.socketio.emit("output", output, namespace="/terminal")

    def shutdown(self):
        kill(self.process_id, SIGKILL)

    def configure_routes(self):
        @self.route(f"/{getenv('ENDPOINT')}")
        def index():
            return render_template("index.html")

        @self.route("/shutdown", methods=["POST"])
        def shutdown():
            return "shutdown"

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
                    command = "telnet 192.168.56.50"
                elif getenv("PASSWORD"):
                    command = (
                        f"sshpass -p {getenv('PASSWORD')} ssh {getenv('OPTIONS')} "
                        f"{getenv('USERNAME')}@{getenv('IP_ADDRESS')} {port}"
                    )
                else:
                    command = f"ssh {getenv('OPTIONS')} {getenv('IP_ADDRESS')} {port}"
                run(command.split())


app = Server()
