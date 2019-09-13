#!/bin/bash

# Run tests on application.
# Show coverage report if all tests pass.

set -o nounset
set -o errexit
set +o xtrace

if [ $# -ne 1 ]; then
    echo "Produce a test coverage report for an application."
    echo "usage: $0 app_name"
    exit 1
fi

export MODULE=$(basename "$1")
command="./manage.py test --failfast --settings=common.settings.testing $MODULE"
echo "$command"
coverage run --branch --source=$MODULE $command
coverage report --show-missing --skip-covered
rm -f .coverage
