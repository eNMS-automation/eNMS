from flask import Blueprint, current_app


settings = {
    "active": True,
    "description": "Custom Command Line Interface for iEN-ap",
    "cli_group": "custom",
}


class Plugin:
    def __init__(
        self,
        url_prefix=None,
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

        @self.blueprint.cli.command("git-pull",)
        def test():
            current_app.logger.info("Test command-line command")


plugin = Plugin(**settings)
