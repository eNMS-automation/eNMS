from flask import render_template, Blueprint


class Plugin:
    def __init__(self, server, controller, **settings):
        super().__init__(server, controller, **settings)
        self.register_routes()

    def register_routes(self):
        blueprint = Blueprint(__name__, __name__, **self.blueprint_settings)

        @blueprint.route("/")
        @self.server.monitor_requests
        def plugin():
            return render_template("template.html")

        self.server.register_blueprint(blueprint, url_prefix=self.url_prefix)
