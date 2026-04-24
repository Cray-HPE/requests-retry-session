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

# Make sure SKIP_RC variable is set
./validate_skip_rc.sh

if [[ $# -eq 0 ]]; then
    CONSTRAINTS_FILE=/dev/null
else
    CONSTRAINTS_FILE=$(mktemp)
    for C in "$@"; do
        echo "$C"
    done >> "${CONSTRAINTS_FILE}"
fi

. /app/venv/bin/activate
# Use --no-index to avoid contacting PyPi, since we pre-cached the images when
# we build our Dockerfile
pip3 install --disable-pip-version-check --no-index --find-links="${PIP_DL_DIR}" /app/requests_retry_session*.whl -c "${CONSTRAINTS_FILE}"
pip3 list --format freeze | tee /app/freeze.txt
if [[ -d /app/freeze ]]; then
    fsize=$(stat -c%s /app/freeze.txt)
    if find /app/freeze \
            -type f \
            -name \*.freeze.txt \
            -size ${fsize}c \
            -exec cmp -s /app/freeze.txt {} \; \
            -print -quit | grep -q .
    then
        # This means our current pip install list matches one we have already
        # tested -- no need to repeat it
        echo "This set of packages has already been tested for this Python version -- SKIPPING"
        exit ${SKIP_RC}
    fi
    # This means this is a new install list, so copy it to the directory
    echo "This set of packages has not been tested yet for this Python version"
    ffile=$(mktemp -p /app/freeze --suffix .freeze.txt)
    cp /app/freeze.txt "${ffile}"
    chmod a+rw "${ffile}"
fi
pushd /app
if ! python -m test_rrs ; then
    # Display log file
    echo "test_rrs FAILED; Showing log file contents"
    cat test_rrs.log
    exit 1
fi
popd
