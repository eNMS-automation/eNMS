from eNMS.controller import Controller
from eNMS.framework import create_app

class App():

    def __init__(self, path):
        self.controller = Controller(path)

    def create_app(self, path)
        return create_app(path)
