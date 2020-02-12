from os import getenv
from eNMS.framework import create_app
from werkzeug.serving import WSGIRequestHandler

app = create_app()

if __name__ == "__main__":
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run(
        debug=True,
        use_debugger=False,
        use_reloader=False,
        passthrough_errors=True,
        port=getenv("FLASK_APP_PORT", 5000),
    )
