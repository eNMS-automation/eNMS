from flask import request, render_template, Blueprint
from .forms import CustomForm

settings = {
    "active": True,
    "name": "Plugin 2",
    "template_folder": "templates",
    "static_folder": "static",
    "pages": {"Plugin 11": {"Form": f"/plugin2/3", }},
    "rbac": {},  # TODO
}


class Plugin:
    def __init__(
        self,
        server,
        controller,
        name="test",
        active=True,
        template_folder=None,
        static_folder=None,
        pages={},
        rbac={},
        cli_group=None,
    ):
        self.server = server
        self.controller = controller
        self.name = "Plugin 2"
        self.active = active
        self.template_folder = template_folder
        self.static_folder = static_folder
        self.pages = pages
        self.rbac = rbac
        self.cli_group = cli_group
        self.init_blueprint()
        self.register_routes()
        self.register_endpoints()

    def init_blueprint(self):
        blueprint = Blueprint(
            f"{__name__}_bp",
            __name__,
            template_folder=self.template_folder,
            static_folder=self.static_folder,
            cli_group=self.cli_group,
        )
        self.server.register_blueprint(
            blueprint, url_prefix="/plugin2"
        )

    def register_routes(self):
        @self.blueprint.route("/<int:page>")
        def plugin(page):
            form = CustomForm(request.form)
            return render_template(f"/custom_{page}.html", page=page, form=form)

    def register_endpoints(self, app):
        @app.register_endpoint
        def process_form_data(self, **data):
            return data["router_id"] * 2
