from flask import render_template, Blueprint


class Plugin:
    def __init__(self, server, controller, **kwargs):
        self.server = server
        self.controller = controller
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.configure_routes()

    def configure_routes(self):
        blueprint = Blueprint(f"{__name__}_bp", __name__, **self.blueprint_settings)

        @blueprint.route("/")
        def plugin():
            return render_template("custom_1.html")

        self.server.register_blueprint(blueprint, url_prefix=self.url_prefix)
