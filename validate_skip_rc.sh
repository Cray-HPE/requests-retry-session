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

# SKIP_RC must be set to the exit code to use in the case when tests are skipped
if [[ ! -v SKIP_RC ]]; then
    echo "ERROR: SKIP_RC environment variable is not set" 1>&2
elif [[ -z ${SKIP_RC} ]]; then
    echo "ERROR: SKIP_RC environment variable is set to an empty value" 1>&2
elif [[ ! "${SKIP_RC}" =~ ^[1-9][0-9]*$ ]]; then
    echo "ERROR: SKIP_RC environment variable is not set to a positive integer value without leading 0s: '${SKIP_RC}'" 1>&2
elif (( SKIP_RC > 255 )); then
    echo "ERROR: SKIP_RC environment variable is set to an integer > 255: '${SKIP_RC}'" 1>&2
else
    exit 0
fi

exit 1
