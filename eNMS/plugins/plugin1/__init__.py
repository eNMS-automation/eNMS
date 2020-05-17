from flask import render_template, Blueprint


class Plugin:
    def __init__(self, server, controller, db, **settings):
        blueprint = Blueprint(__name__, __name__, **settings["blueprint"])

        @blueprint.route("/")
        @server.monitor_requests
        def plugin():
            return render_template("template.html")

        server.register_blueprint(blueprint, url_prefix=settings["url_prefix"])
