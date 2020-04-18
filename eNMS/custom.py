from flask import Blueprint, render_template


class CustomController:
    @staticmethod
    def configure_customization(blueprint):
        @blueprint.route("/custom_page/<int:page>")
        def custom_page(page):
            return render_template("custom.html", page=page)

    def endpoint(self):
        return True
