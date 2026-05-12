from flask import Flask

from app.api.routes import api_bp
from app.core.config import get_settings
from app.core.container import build_container
from app.ui.routes import ui_bp


def create_app() -> Flask:
    settings = get_settings()
    app = Flask(
        __name__,
        template_folder="../ui/templates",
        static_folder="../ui/static",
    )
    app.config.update(
        APP_NAME=settings.app_name,
        DEBUG=settings.debug,
        HOST=settings.host,
        PORT=settings.port,
    )
    app.extensions["container"] = build_container(settings)
    app.register_blueprint(api_bp)
    app.register_blueprint(ui_bp)
    return app
