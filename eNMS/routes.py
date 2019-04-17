from flask_wtf import FlaskForm
from json.decoder import JSONDecodeError
from logging import info
from flask import jsonify, redirect, request, url_for
from flask_login import current_user
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from typing import List, Union
from werkzeug.wrappers import Response

from eNMS import db
from eNMS.classes import classes
from eNMS.extensions import bp
from eNMS.forms import form_classes, form_templates
from eNMS.functions import delete, factory, fetch, fetch_all_visible, get, post
from eNMS.properties import table_fixed_columns, table_properties


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("bp.login"))


@bp.route("/login", methods=["GET", "POST"])
def login() -> Union[Response, str]:
    if request.method == "POST":
        name, password = request.form["name"], request.form["password"]
        try:
            if request.form["authentication_method"] == "Local User":
                user = fetch("User", name=name)
                if user and password == user.password:
                    login_user(user)
                    return redirect(url_for("home_blueprint.dashboard"))
            elif request.form["authentication_method"] == "LDAP Domain":
                with Connection(
                    ldap_client,
                    user=f'{app.config["LDAP_USERDN"]}\\{name}',
                    password=password,
                    auto_bind=True,
                    authentication=NTLM,
                ) as connection:
                    connection.search(
                        app.config["LDAP_BASEDN"],
                        f"(&(objectClass=person)(samaccountname={name}))",
                        search_scope=SUBTREE,
                        get_operational_attributes=True,
                        attributes=["cn", "memberOf", "mail"],
                    )
                    json_response = loads(connection.response_to_json())["entries"][0]
                    if json_response:
                        user = {
                            "name": name,
                            "password": password,
                            "email": json_response["attributes"].get("mail", ""),
                        }
                        if any(
                            group in s
                            for group in app.config["LDAP_ADMIN_GROUP"]
                            for s in json_response["attributes"]["memberOf"]
                        ):
                            user["permissions"] = ["Admin"]
                        new_user = factory("User", **user)
                        login_user(new_user)
                        return redirect(url_for("dashboard"))
            elif request.form["authentication_method"] == "TACACS":
                if tacacs_client.authenticate(name, password).valid:
                    user = factory("User", **{"name": name, "password": password})
                    login_user(user)
                    return redirect(url_for("dashboard"))
            abort(403)
        except Exception as e:
            info(f"Authentication failed ({str(e)})")
            abort(403)
    if not current_user.is_authenticated:
        login_form = LoginForm(request.form)
        authentication_methods = [("Local User",) * 2]
        if USE_LDAP:
            authentication_methods.append(("LDAP Domain",) * 2)
        if USE_TACACS:
            authentication_methods.append(("TACACS",) * 2)
        login_form.authentication_method.choices = authentication_methods
        return render_template("pages/login.html", login_form=login_form)
    return redirect(url_for("dashboard"))


@get("/<form_type>_form", "View")
def route_form(form_type: str) -> dict:
    return dict(
        form=form_classes.get(form_type, FlaskForm)(request.form),
        form_type=form_type,
        template=f"forms/{form_templates.get(form_type, form_type + '_form')}",
    )


@get("/<_>/<table_type>_management", "View")
def route_table(_: str, table_type: str) -> dict:
    return dict(
        properties=table_properties[table_type],
        fixed_columns=table_fixed_columns[table_type],
        type=table_type,
        template="table",
    )


@get("/filtering/<table>")
def filtering(table: str) -> Response:
    model = classes.get(table, classes["Device"])
    properties = table_properties[table]
    if table in ("configuration", "device"):
        properties.append("current_configuration")
    try:
        order_property = properties[int(request.args["order[0][column]"])]
    except IndexError:
        order_property = "name"
    order = getattr(getattr(model, order_property), request.args["order[0][dir]"])()
    constraints = []
    for property in properties:
        value = request.args.get(f"form[{property}]")
        if value:
            constraints.append(getattr(model, property).contains(value))
    result = db.session.query(model).filter(and_(*constraints)).order_by(order)
    if table in ("device", "link", "configuration"):
        pools = [int(id) for id in request.args.getlist("form[pools][]")]
        if pools:
            result = result.filter(model.pools.any(classes["pool"].id.in_(pools)))
    return jsonify(
        {
            "draw": int(request.args["draw"]),
            "recordsTotal": len(model.query.all()),
            "recordsFiltered": len(result.all()),
            "data": [
                [getattr(obj, property) for property in properties]
                + obj.generate_row(table)
                for obj in result.limit(int(request.args["length"]))
                .offset(int(request.args["start"]))
                .all()
            ],
        }
    )


@post("/get/<cls>/<id>", "View")
def get_instance(cls: str, id: str) -> dict:
    instance = fetch(cls, id=id)
    info(f"{current_user.name}: GET {cls} {instance.name} ({id})")
    return instance.serialized


@post("/get_all/<cls>", "View")
def get_all_instances(cls: str) -> List[dict]:
    info(f"{current_user.name}: GET ALL {cls}")
    return [instance.get_properties() for instance in fetch_all_visible(cls)]


@post("/update/<cls>", "Edit")
def update_instance(cls: str) -> dict:
    try:
        instance = factory(cls, **request.form)
        info(f"{current_user.name}: UPDATE {cls} " f"{instance.name} ({instance.id})")
        return instance.serialized
    except JSONDecodeError:
        return {"error": "Invalid JSON syntax (JSON field)"}
    except IntegrityError:
        return {"error": "An object with the same name already exists"}


@post("/delete/<cls>/<id>", "Edit")
def delete_instance(cls: str, id: str) -> dict:
    instance = delete(cls, id=id)
    info(f'{current_user.name}: DELETE {cls} {instance["name"]} ({id})')
    return instance


@post("/shutdown", "Admin")
def shutdown() -> str:
    info(f"{current_user.name}: SHUTDOWN eNMS")
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()
    return "Server shutting down..."
