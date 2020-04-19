from flask import Blueprint, render_template, request

from eNMS.custom.forms import CustomForm


def set_custom_routes(blueprint):
    @blueprint.route("/custom_page/<int:page>")
    def custom_page(page):
        form = CustomForm(request.form) if page == 2 else None
        return render_template(f"custom/custom_{page}.html", page=page, form=form)
