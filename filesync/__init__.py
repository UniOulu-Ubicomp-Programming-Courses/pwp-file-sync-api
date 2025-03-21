import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger

db = SQLAlchemy()

# Based on http://flask.pocoo.org/docs/1.0/tutorial/factory/#the-application-factory
# Modified to use Flask SQLAlchemy
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SERVER_NAME="localhost",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SWAGGER={
            "title": "FileSync API",
            "openapi": "3.0.4",
            "uiversion": 3,
            "doc_dir": "filesync/doc"
        }
    )

    if test_config is None:
        app.config.from_pyfile("config/config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    from . import management
    from . import api
    from filesync.utils import SyncedFileConverter
    app.cli.add_command(management.init_db_command)
    app.cli.add_command(management.generate_test_data)
    app.cli.add_command(management.update_schemas)
    app.cli.add_command(management.update_docs)
    app.url_map.converters["syncfile"] = SyncedFileConverter
    app.register_blueprint(api.api_bp)
    swagger = Swagger(app, template_file="doc/base.yml")

    return app
