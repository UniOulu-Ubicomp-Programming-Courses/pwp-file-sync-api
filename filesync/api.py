import json
import yaml
from flask import Blueprint, Response
from flask_restful import Api
from filesync.resources import syncfile

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api.add_resource(syncfile.SyncedFileCollection, "/files/")
api.add_resource(syncfile.SyncedFileItem, "/files/<syncfile:syncfile>/")

@api_bp.route("/")
def entry():
    with open("filesync/doc/base.yml") as source:
        doc = yaml.safe_load(source)
    return Response(json.dumps({"api_version": doc["info"]["version"], "api_name": "filesync"}), 200)
