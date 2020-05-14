from flask import render_template, Blueprint


class Plugin:
    def __init__(self, server, controller, **kwargs):
        self.server = server
        self.controller = controller
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.register_routes()

    def register_routes(self):
        blueprint = Blueprint(f"{__name__}_bp", __name__, **self.blueprint_settings)

        @blueprint.route("/")
        def plugin():
            return render_template("template.html")

        self.server.register_blueprint(blueprint, url_prefix=self.url_prefix)
