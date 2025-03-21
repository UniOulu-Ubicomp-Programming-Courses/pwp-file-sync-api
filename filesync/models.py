import base64
import datetime
import click
import hashlib
from flask.cli import with_appcontext
from sqlalchemy.orm import deferred
from filesync import db


class SyncedFile(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    handle = db.Column(db.String(32), nullable=False, unique=True)
    filename = db.Column(db.String(32), nullable=True)
    content = deferred(db.Column(db.LargeBinary, nullable=False, unique=True))
    modified = db.Column(db.DateTime, nullable=False)
    size = db.Column(db.Integer, nullable=False)

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["handle", "content"]
        }
        props = schema["properties"] = {}
        props["handle"] = {
            "description": "File's unique handle",
            "type": "string"
        }
        props["filename"] = {
            "description": "Default filename",
            "type": "string"
        }
        props["content"] = {
            "description": "File content (bytestring)",
            "type": "string"
        }
        return schema

    @classmethod
    def serialize_all(cls):
        for item in cls.query.all():
            yield {
                "handle": item.handle,
                "filename": item.filename,
                "modified": item.modified.isoformat(),
                "size": item.size,
            }


    def serialize(self):
        return {
            "handle": self.handle,
            "filename": self.filename,
            "content": base64.b64encode(self.content).decode("utf-8"),
            "modified": self.modified.isoformat(),
            "size": self.size,
        }

    def deserialize(self, data):
        self.handle = data["handle"]
        self.filename = data.get("filename")
        self.content = base64.b64decode(data["content"])
        self.modified = datetime.datetime.now()
        self.size = len(self.content)
