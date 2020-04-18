from flask import Blueprint, render_template


class CustomController:
    def endpoint(self):
        return True

    @staticmethod
    def configure_customization(blueprint):
        @blueprint.route("/custom_page/<int:page>")
        def custom_page(page):
            return render_template("custom.html", page=page)