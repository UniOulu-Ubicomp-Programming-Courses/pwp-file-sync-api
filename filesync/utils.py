from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.routing import BaseConverter
from filesync.models import SyncedFile

class SyncedFileConverter(BaseConverter):

    def to_python(self, file_handle):
        db_file = SyncedFile.query.filter_by(handle=file_handle).first()
        if db_file is None:
            raise NotFound
        return db_file

    def to_url(self, db_file):
        return db_file.handle
