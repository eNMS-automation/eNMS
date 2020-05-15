class Plugin:
    def __init__(self, server, controller, **kwargs):
        self.server = server
        self.controller = controller
        self.__dict__.update(kwargs)
