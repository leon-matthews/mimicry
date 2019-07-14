
Mimicry is a command-line utility to identify and remove duplicate files,
even across non-connected removable drives.

Interactive use is fast, as a cache of file metadata is used.


Design
======

The first step is always to read metadata about a certain folder tree into a small
database file in the root of that tree. The folder tree is often the root of a removable
drive, but can be anywhere.

1. Iterate recursively through entire folder tree to count files and collect
   data for accurate progress reporting later.
2. Iterate through the tree again, slowly this time. Read every file's metadata, then
   calculate a sha256 hash of its contents. This can be slow. Like a couple of days
   slow.


License
=======

Licensed under the GPL version 3. Basically, this means I let everybody use and share the
program freely, so long as you promise to do the same. See LICENSE.txt for the legalese.
