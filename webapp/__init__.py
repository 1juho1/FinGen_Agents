from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    from . import routes  # noqa: WPS433

    routes.init_app(app)
    return app
