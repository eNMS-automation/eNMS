from flask import abort, jsonify, request, render_template
from flask.wrappers import Response
from flask_login import current_user, login_required
from functools import wraps
from logging import info
from sqlalchemy import exc
from typing import Any, Callable, Generator, List, Optional, Tuple

from eNMS.modules import bp, db
from eNMS.models import classes


def fetch(model: str, **kwargs: Any) -> db.Model:
    return db.session.query(classes[model]).filter_by(**kwargs).first()


def fetch_all(model: str) -> Tuple[db.Model]:
    return classes[model].query.all()


def fetch_all_visible(model: str) -> List[db.Model]:
    return [instance for instance in classes[model].query.all() if instance.visible]


def objectify(model: str, object_list: List[int]) -> List[db.Model]:
    return [fetch(model, id=object_id) for object_id in object_list]


def delete(model: str, **kwargs: Any) -> dict:
    instance = db.session.query(classes[model]).filter_by(**kwargs).first()
    if hasattr(instance, "type") and instance.type == "Task":
        instance.delete_task()
    serialized_instance = instance.serialized
    db.session.delete(instance)
    db.session.commit()
    return serialized_instance


def delete_all(*models: str) -> None:
    for model in models:
        for instance in fetch_all(model):
            delete(model, id=instance.id)
    db.session.commit()


def choices(model: str) -> List[Tuple[int, str]]:
    return [(instance.id, str(instance)) for instance in classes[model].visible()]


def export(model: str) -> List[dict]:
    return [instance.to_dict(export=True) for instance in classes[model].visible()]


def get_one(model: str) -> db.Model:
    return classes[model].query.one()


def factory(cls_name: str, **kwargs: Any) -> db.Model:
    if "id" in kwargs:
        if kwargs["id"]:
            instance = fetch(cls_name, id=kwargs["id"])
        else:
            instance = kwargs.pop("id")
    else:
        instance = fetch(cls_name, name=kwargs["name"])
    if instance:
        instance.update(**kwargs)
    else:
        instance = classes[cls_name](**kwargs)
        db.session.add(instance)
    db.session.commit()
    return instance


def integrity_rollback(function: Callable) -> Callable:
    def wrapper(*a: Any, **kw: Any) -> None:
        try:
            function(*a, **kw)
        except (exc.IntegrityError, exc.InvalidRequestError):
            db.session.rollback()

    return wrapper


def permission_required(permission: Optional[str], redirect: bool = True) -> Callable:
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Response:
            if permission and not current_user.allowed(permission):
                if redirect:
                    abort(403)
                else:
                    return jsonify(False)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get(
    url: str, permission: Optional[str] = None, method: List[str] = ["GET"]
) -> Callable[[Callable], Callable]:
    def outer(func: Callable) -> Callable:
        @bp.route(url, methods=method)
        @login_required
        @permission_required(permission)
        @wraps(func)
        def inner(*args: Any, **kwargs: Any) -> Response:
            ctx = func(*args, **kwargs) or {}
            if not isinstance(ctx, dict):
                return ctx
            if request.url is not None:
                endpoint = request.url.split("/")[-1]
            ctx["endpoint"] = endpoint
            info(
                f"User '{current_user.name}' ({request.remote_addr})"
                f"calling the endpoint {url} (GET)"
            )
            return render_template(
                f"{ctx.pop('template', 'pages/' + endpoint)}.html", **ctx
            )

        return inner

    return outer


def post(url: str, permission: Optional[str] = None) -> Callable[[Callable], Callable]:
    def outer(func: Callable) -> Callable:
        @bp.route(url, methods=["POST"])
        @login_required
        @permission_required(permission, redirect=False)
        @wraps(func)
        def inner(*args: Any, **kwargs: Any) -> Response:
            data = {**request.form.to_dict(), **{"creator": current_user.id}}
            for property in data.get("list_fields", "").split(","):
                data[property] = request.form.getlist(property)
            for property in data.get("boolean_fields", "").split(","):
                data[property] = property in request.form
            request.form = data
            info(
                f"User '{current_user.name}' ({request.remote_addr})"
                f" calling the endpoint {request.url} (POST)"
            )
            try:
                result = func(*args, **kwargs)
                db.session.commit()
                return jsonify(result)
            except Exception as e:
                return jsonify({"error": str(e)})

        return inner

    return outer
