
========
Concepts
========


Different kinds of duplicates
=============================

Excluding backups, exactly one copy of each file is desired.  Duplicates should
be deleted to free up space for other content.

There are different kinds of duplicates.  It's probably not practical for this
program to find all the types, but we should at least be clear about what our
goals are, and where conflicts may arise.

Same content, different folder, unwanted duplicates.
    For example, mulitiple copies of the same file. Delete second and
    further copies.

Same content, different folder, necessary copies.
    For example, license files.  Leave duplicates alone.

Same name, different extension and content.
    Even though they are not the same file from a computer's point of view,
    having two copies of the same song with different physical and naming
    formats is probably undesired too.


Minimising work
===============

Finding identical content
-------------------------

To find files with identical content, it should not be necessary to
calculate the hash for every file of interest.

Use a two pass method:

1. First read metadata from every file, including their sizes.
2. Then calculate the hash just those files whose size's are exactly the same.

Cache
-----

Calculating the SHA1 is extremely time consuming.  Once calculated a file's
hash is saved into an SQLite database.  Next time it's needed, use the cached
value if the files mtime, size and name are unchanged -- unless it's been too
long (week? month? year?).

Reading directories only
------------------------

The `mlocate` project uses an optimisation in their `updatedb` program where
only directory metadata need to be read to keep their database up-to-date.
Investigation of its documentation (and the system calls it makes) shows that
this is done by comparing the mtime/ctime of each directory with the database
copy.  If they differ, then the contents of the directory is re-read.

This works because the directory mtime will be changed if files are added,
renamed, or deleted.  Unfortunately it does *not* change if a file in the
directory is modified.  This is fine for `mlocate`, as it is only concerned
with file names, but makes the technique useless for us.


Find duplicates via SQL query
==============================

We can find duplicates via SHA1 collisions using SQL from the
command-line as follows::

    echo "SELECT * from files where sha1 in (SELECT sha1 FROM files "
        "GROUP BY sha1 HAVING count(*) > 1);" | sqlite3 files.db
