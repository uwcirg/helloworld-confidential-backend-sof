from flask import Flask

from backend.api import base_blueprint
from backend.auth import auth_blueprint
from backend.extensions import oauth


def create_app(testing=False, cli=False):
    """Application factory, used to create application
    """
    app = Flask('backend')
    app.config.from_object('backend.config')

    configure_extensions(app, cli)
    register_blueprints(app)

    return app


def configure_extensions(app, cli):
    """configure flask extensions
    """
    oauth.init_app(app)


def register_blueprints(app):
    """register all blueprints for application
    """
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(base_blueprint)
