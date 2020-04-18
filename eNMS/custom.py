from flask import Blueprint, render_template


class CustomController:
    @staticmethod
    def set_custom_routes(blueprint):
        @blueprint.route("/custom_page/<int:page>")
        def custom_page(page):
            return render_template(f"custom/custom_{page}.html", page=page)

    def endpoint(self):
        return True
