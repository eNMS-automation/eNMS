from flask import request, render_template, Blueprint
from .forms import Form


class Plugin:
    def __init__(self, server, controller, **kwargs):
        self.server = server
        self.controller = controller
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.register_routes()
        self.register_endpoints()

    def register_routes(self):
        blueprint = Blueprint(f"{__name__}_bp", __name__, **self.blueprint_settings)

        @blueprint.route("/form")
        def plugin():
            return render_template(f"/custom_{page}.html", form=Form(request.form))

        self.server.register_blueprint(blueprint, url_prefix=self.url_prefix)

    def register_endpoints(self):
        @self.controller.register_endpoint
        def process_form_data(self, **data):
            return int(data["router_id"]) * 2
