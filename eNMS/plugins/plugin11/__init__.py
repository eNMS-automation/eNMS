from flask import request, render_template, Blueprint
from .forms import CustomForm

settings = {
    "active": True,
    "description": "Plugin 11 - test plugin",
    "url_prefix": "/plugin11",
    "template_folder": "templates",
    "static_folder": "static",
    "pages": {"Plugin 11": {"Form": f"/plugin11/3", }},
    "rbac": {},  # TODO
}


class Plugin:
    def __init__(
        self,
        url_prefix,
        active=True,
        description="",
        template_folder=None,
        static_folder=None,
        pages={},
        rbac={},
        cli_group=None,
    ):

        self.active = active
        self.description = description
        self.url_prefix = url_prefix
        self.template_folder = template_folder
        self.static_folder = static_folder
        self.pages = pages
        self.rbac = rbac
        self.cli_group = cli_group
        self.init_blueprint()

    def init_blueprint(self):
        self.blueprint = Blueprint(
            f"{__name__}_bp",
            __name__,
            template_folder=self.template_folder,
            static_folder=self.static_folder,
            cli_group=self.cli_group,
        )

        @self.blueprint.route("/<int:page>")
        def plugin(page):
            form = CustomForm(request.form)
            return render_template(f"/custom_{page}.html", page=page, form=form)


plugin = Plugin(**settings)
