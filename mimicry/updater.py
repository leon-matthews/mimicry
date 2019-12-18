

class Updater:
    """
    Create or update database from mounted file tree.
    """

    def __init__(self, root):
        self.root = root

    def update(self):
        """
        Update and create database records for all files under given root.

        Returns number of file records updated.
        """
        files_updated = 0
        for root, dirs, files in os.walk(self.root):
            root = os.path.abspath(root)
            dirs.sort(key=str.lower)
            files.sort(key=str.lower)

            for name in files:
                path = os.path.join(root, name)
                logger.debug("Add %r", path)
                was_updated = self.db.add(path)
                if was_updated:
                    files_updated += 1

        return files_updated

    def _update_file(self, path):
        """
        Examines file in path, skipping re-calculating the sha256 hash if the
        name and mtime of the file are unchanged from the cache record.

        Returns True if file record was updated, False otherwise.
        """
        # Load file metadata from disk (without sha256 for now)
        local_file = File(path=path)

        # Compare file with file from cache.  Skip if mtime the same.
        try:
            cached_file = self.db.load(path)
        except UnicodeEncodeError:
            print(repr(path))
            raise
        if cached_file and cached_file.mtime == local_file.mtime:
            return False

        # Calculate hash, save to db
        print("+{}".format(path))
        local_file.from_file(path, calculate_hash=True)
        self.db.save(local_file)
        return True
