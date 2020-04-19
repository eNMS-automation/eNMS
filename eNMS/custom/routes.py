from flask import Blueprint, render_template, request

from eNMS.custom.forms import CustomForm


def set_custom_routes(blueprint):
    @blueprint.route("/custom_page/<int:page>")
    def custom_page(page):
        kwargs = {"form": CustomForm(request.form), "form_type": "custom"} if page == 2 else {}
        return render_template(f"custom/custom_{page}.html", page=page, **kwargs)
