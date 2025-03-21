"""
This module contains CLI commands for management. Available commands:
* init-db: initializes the database
* testgen: populates the database with random data for development purposes
* update-schemas: Updates schemas in the API documentation's component section
* update-docs: Updates endpoint docs
"""

import copy
import click
import datetime
import hashlib
import os.path
import yaml
from slugify import slugify
from flask import current_app, url_for
from flask.cli import with_appcontext
from filesync import db
from filesync.models import SyncedFile
from filesync.resources import syncfile

CONTENT_1 = b"donkeyswings"
TEST_FILE_1 = {
    "handle": "file-1",
    "filename": "file-1.txt",
    "content": CONTENT_1,
    "modified": datetime.datetime(2024, 12, 12, 12, 0, 0),
    "size": len(CONTENT_1)
}
CONTENT_2 = hashlib.sha256(b"donkeyswings").digest()
TEST_FILE_2 = {
    "handle": "file-2",
    "filename": "file-2.bin",
    "content": CONTENT_2,
    "modified": datetime.datetime(2030, 12, 12, 12, 0, 0),
    "size": len(CONTENT_2)
}


class literal_unicode(str): pass

def literal_unicode_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')
yaml.add_representer(literal_unicode, literal_unicode_representer)


@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()

@click.command("testgen")
@with_appcontext
def generate_test_data():
    file_1 = SyncedFile(**TEST_FILE_1)
    file_2 = SyncedFile(**TEST_FILE_2)
    db.session.add(file_1)
    db.session.add(file_2)
    db.session.commit()

@click.command("update-schemas")
def update_schemas():

    with open("filesync/doc/base.yml") as source:
        doc = yaml.safe_load(source)
    schemas = doc["components"]["schemas"] = {}
    for cls in [SyncedFile]:
        schemas[cls.__name__] = cls.json_schema()

    doc["info"]["description"] = literal_unicode(doc["info"]["description"])
    with open("filesync/doc/base.yml", "w") as target:
        target.write("---\n")
        target.write(yaml.dump(doc, default_flow_style=False))

@click.command("update-docs")
@with_appcontext
def update_docs():
    DOC_ROOT = "./filesync/doc/"
    GET_TEMPLATE = {
        "responses": {
            "200": {
                "content": {
                    "application/json": {},
                    "application/vnd.mason+json": {}
                }
            }
        }
    }
    POST_PUT_TEMPLATE = {
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {}
                }
            }
        }
    }
    POST_TEMPLATE = POST_PUT_TEMPLATE.copy()
    POST_TEMPLATE["responses"] = {
        "201": {
            "headers": {
                "Location": {
                    "description": "URI of the created resource",
                    "schema": {
                        "type": "string"
                    }
                }
            }
        }
    }
    DELETE_TEMPLATE = {
        "responses": {
            "204": {
                "description": "Successfully deleted"
            },
            "404": {
                "description": "Object not found"
            }
        }
    }

    resource_classes = [syncfile.SyncedFileCollection, syncfile.SyncedFileItem]

    client = current_app.test_client()

    def read_or_create(path, template={}):
        if os.path.exists(path):
            with open(path) as source:
                doc = yaml.safe_load(source)
        else:
            doc = copy.deepcopy(template)

        return doc

    def write_doc(path, content):
        with open(path, "w") as target:
            target.write("---\n")
            target.write(yaml.dump(doc, default_flow_style=False))

    for cls in resource_classes:
        endpoint = cls.__name__.lower()
        endpoint_path = os.path.join(DOC_ROOT, endpoint)
        os.makedirs(endpoint_path, exist_ok=True)
        if hasattr(cls, "get"):
            doc_path = os.path.join(endpoint_path, "get.yml")
            doc = read_or_create(doc_path, GET_TEMPLATE)
            uri = url_for(
                "api." + endpoint,
                syncfile=SyncedFile(**TEST_FILE_1),
            )
            doc["responses"]["200"]["content"]["application/json"]["example"] = client.get(uri).json
            write_doc(doc_path, doc)

        if hasattr(cls, "post"):
            doc_path = os.path.join(endpoint_path, "post.yml")
            doc = read_or_create(doc_path, POST_TEMPLATE)
            doc["requestBody"]["content"]["application/json"]["schema"]["$ref"] = (
                f"#/components/schemas/{cls.child_model.__name__}"
            )
            write_doc(doc_path, doc)

        if hasattr(cls, "put"):
            doc_path = os.path.join(endpoint_path, "put.yml")
            doc = read_or_create(doc_path, POST_PUT_TEMPLATE)
            doc["requestBody"]["content"]["application/json"]["schema"]["$ref"] = (
                f"#/components/schemas/{cls.model.__name__}"
            )
            write_doc(doc_path, doc)

        if hasattr(cls, "delete"):
            doc_path = os.path.join(endpoint_path, "delete.yml")
            doc = read_or_create(doc_path, DELETE_TEMPLATE)
            write_doc(doc_path, doc)
