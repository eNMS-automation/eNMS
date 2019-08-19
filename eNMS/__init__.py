from eNMS.controller import controller
from eNMS.framework import create_app


class App():

    def __init__(self, path):
        self.path = path
        print(path)
        controller.init_app(path)

    def create_web_app(self):
        return create_app(self.path)
