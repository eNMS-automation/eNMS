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


app = Server()
