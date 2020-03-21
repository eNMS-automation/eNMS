from datetime import datetime
from flask import request

from functools import wraps
from uuid import getnode

from eNMS import app
from eNMS.database import Session
from eNMS.database.functions import delete, factory, fetch





def create_app_resources():
    endpoints = {}
    for endpoint in app.rest_endpoints:

        def post(_, ep=endpoint):
            getattr(app, ep)()
            Session.commit()
            return f"Endpoint {ep} successfully executed."

        endpoints[endpoint] = type(
            endpoint,
            (Resource,),
            {"decorators": [auth.login_required, catch_exceptions], "post": post},
        )
    return endpoints
