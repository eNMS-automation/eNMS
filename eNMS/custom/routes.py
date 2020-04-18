from flask import Blueprint, render_template


def configure_customization(server):

    blueprint = Blueprint("custom", __name__, template_folder="../../templates")

    @blueprint.route("/custom_page/<int:page>")
    def custom_page(page):
        print("aaaa" * 1000)
        return render_template("custom.html", page=page)

    server.register_blueprint(blueprint)
