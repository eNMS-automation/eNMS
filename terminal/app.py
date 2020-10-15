from flask import Flask, render_template
from flask_socketio import SocketIO
from os import getenv, read, write
from pty import fork
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
            output = read(self.file_descriptor, 1024).decode()
            self.socketio.emit("output", output, namespace="/terminal")

    def configure_routes(self):
        @self.route(f"/{getenv('ENDPOINT')}")
        def index():
            return render_template("index.html")

        @self.socketio.on("input", namespace="/terminal")
        def input(data):
            write(self.file_descriptor, data.encode())

        @self.socketio.on("connect", namespace="/terminal")
        def connect():
            self.process_id, self.file_descriptor = fork()
            if self.process_id:
                self.socketio.start_background_task(target=self.send_data)
            else:
                if getenv("PROTOCOL") == "telnet":
                    command = "telnet 192.168.56.50"
                else:
                    command = f"sshpass -p admin ssh {getenv('OPTIONS')} admin@192.168.56.50"
                run(command.split())


app = Server()
