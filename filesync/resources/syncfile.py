import json
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from filesync.models import SyncedFile


class SyncedFileCollection(Resource):

    child_model = SyncedFile

    def get(self):
        body = {
            "files": list(SyncedFile.serialize_all()),
        }
        return Response(json.dumps(body), 200)

    def post(self):
        try:
            validate(request.json, SyncedFile.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        syncfile = SyncedFile()
        syncfile.deserialize(request.json)
        try:
            db.session.add(syncfile)
            db.session.commit()
        except IntegrityError:
            raise Conflict(f"Synced file with handle '{request.json["handle"]}' already exists.")

        return Response(status=201, headers={
            "Location": url_for("api.syncedfileitem", syncfile=syncfile)
        })


class SyncedFileItem(Resource):

    model = SyncedFile

    def get(self, syncfile):
        body = syncfile.serialize()
        return Response(json.dumps(body), 200)

    def put(self, syncfile):
        try:
            validate(request.json, SyncedFile.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))



    def delete(self, syncfile):
        pass


