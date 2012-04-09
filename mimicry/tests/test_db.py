
import tempfile
from unittest import TestCase

from ..db import DB
from ..file import File


class TestDB(TestCase):
    def test_empty(self):
        "Operations work as expected on empty database"
        db = DB()
        self.assertEqual(db.count(), 0)
        self.assertEqual(db.count_bytes(), 0)
        self.assertEqual(list(db.files()), [])

    def test_save_and_load(self):
        "Simple save and load operations"
        db = DB()
        with tempfile.NamedTemporaryFile(prefix='mimicry-') as tmp:
            # Save file's metadata to db...
            path = tmp.name
            f = File(path)
            db.save(f)

            # ...and load it back
            f2 = db.load(path)
            self.assertEqual(f, f2)
