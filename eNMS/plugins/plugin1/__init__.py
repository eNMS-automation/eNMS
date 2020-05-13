from flask import render_template, Blueprint


settings = {
    "active": True,
    "name": "Plugin 1",
    "url_prefix": "/plugin1",
    "template_folder": "templates",
    "static_folder": "static",
    "pages": {"Plugin 10": "/plugin1/"},
}


class Plugin:
    def __init__(self, server, controller, **kwargs):
        self.server = server
        self.controller = controller
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.init_blueprint()

    def init_blueprint(self):
        self.blueprint = Blueprint(
            f"{__name__}_bp",
            __name__,
            template_folder=self.template_folder,
            static_folder=self.static_folder,
        )
        

        @self.blueprint.route("/")
        def plugin():
            return render_template("custom_1.html")
        
        self.server.register_blueprint(self.blueprint, url_prefix="/plugin1")
