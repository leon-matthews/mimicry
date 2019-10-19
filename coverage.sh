#!/bin/bash

# Run tests on application.
# Show coverage report if all tests pass.

set -o nounset
set -o errexit
set +o xtrace

if [ $# -ne 0 ]; then
    echo "Produce a coverage report for unit tests"
    echo "usage: $0"
    exit 1
fi

COVERAGE=coverage-3.7

$COVERAGE run --branch --module unittest --failfast --catch
$COVERAGE report --show-missing
rm -f .coverage
