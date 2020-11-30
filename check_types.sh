#!/bin/bash

# Run 'mypy' type checker on application.

set -o nounset
set -o errexit
set +o xtrace


mypy -p mimicry --pretty --sqlite-cache --txt-report . && cat index.txt
rm -f index.txt
