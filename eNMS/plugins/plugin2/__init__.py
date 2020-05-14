from flask import request, render_template, Blueprint
from .forms import CustomForm


class Plugin:
    def __init__(self, server, controller, **kwargs):
        self.server = server
        self.controller = controller
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.init_blueprint()
        self.register_routes()
        self.register_endpoints()

    def init_blueprint(self):
        self.blueprint = Blueprint(
            f"{__name__}_bp", __name__, **self.blueprint_settings
        )

    def register_routes(self):
        @self.blueprint.route("/<int:page>")
        def plugin(page):
            form = CustomForm(request.form)
            return render_template(f"/custom_{page}.html", page=page, form=form)

        self.server.register_blueprint(self.blueprint, url_prefix="/plugin2")

    def register_endpoints(self):
        @self.controller.register_endpoint
        def process_form_data(self, **data):
            return data["router_id"] * 2
