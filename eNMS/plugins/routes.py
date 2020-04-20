from flask import render_template, request

from eNMS.plugins.forms import CustomForm


def set_custom_routes(blueprint):
    @blueprint.route("/plugin/<int:page>")
    def plugin(page):
        form = CustomForm(request.form) if page == 2 else None
        return render_template(f"plugins/custom_{page}.html", page=page, form=form)
