from flask import render_template, Blueprint


settings = {
    "active": True,
    "name": "Plugin 1",
    "template_folder": "templates",
    "static_folder": "static",
    "pages": {"Plugin 10": "/plugin1/"},
}


class Plugin:
    def __init__(
        self,
        server,
        controller,
        name="test",
        active=True,
        description="",
        template_folder=None,
        static_folder=None,
        pages={},
    ):
        self.server = server
        self.controller = controller
        self.name = "Plugin 1"
        self.active = active
        self.template_folder = template_folder
        self.static_folder = static_folder
        self.pages = pages
        self.init_blueprint()

    def init_blueprint(self):
        blueprint = Blueprint(
            f"{__name__}_bp",
            __name__,
            template_folder=self.template_folder,
            static_folder=self.static_folder,
        )
        self.server.register_blueprint(
            blueprint, url_prefix="/plugin1"
        )

        @self.blueprint.route("/")
        def plugin():
            return render_template("custom_1.html")
