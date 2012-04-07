#!/bin/bash


# Check that 'inotifywait' is installed
if ! which inotifywait
then
    echo "The 'inotifywait' command is not installed."
    echo
    echo "If you're running Linux, please install the 'inotify-tools' package,"
    echo "and try again.  (eg. 'sudo apt-get install inotify-tools')"
    echo
    echo "If you're *not* running Linux you'll just have to run 'make html' "
    echo "yourself manually after each edit...  Sorry."
    exit 1
fi


# Command loop
make clean
while true;
do
    # Run commands
    clear
    time make html

    # Block until file system changed under current working directory
    echo
    echo "Watching filesystem for changes"
    inotifywait -q -e create,delete,modify,move -r ..
done
