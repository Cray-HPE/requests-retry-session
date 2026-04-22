#!/bin/bash
#
# MIT License
#
# (C) Copyright 2026 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#

# Usage: test_rrs.sh [constraint1] [constraint2] ...
# The constraints are specified when doing the pip install

set -euo pipefail

if [[ $# -eq 0 ]]; then
    CONSTRAINTS_FILE=/dev/null
else
    CONSTRAINTS_FILE=$(mktemp)
    for C in "$@"; do
        echo "$C"
    done >> "${CONSTRAINTS_FILE}"
fi

. /app/venv/bin/activate
pip3 install --disable-pip-version-check --no-cache-dir /app/requests_retry_session*.whl -c "${CONSTRAINTS_FILE}"
pip3 list --format freeze
python /app/test_rrs.py
