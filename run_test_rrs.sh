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

set -euo pipefail

IMG="pytest-${PY_VERSION}:${DOCKER_VERSION}"
constfile=$(mktemp)
summfile=$(mktemp)
pip_freeze_dir=$(mktemp -d)

python3 ./gen_test_constraints.py > "${constfile}"
mapfile -t lines < "${constfile}"

total=0
failed=0

for ARGS in "${lines[@]}"; do
    # Deliberately do not quote $ARGS, so it is split into multiple arguments
    # if there is whitespace in it, or it will not be an argument at all,
    # if it is empty
    echo "###############################################################"
    echo "#"
    echo "# Testing ${PY_VERSION} with constraints $ARGS"
    echo "#"
    echo "###############################################################"
    let total+=1
    if docker run -v "${pip_freeze_dir}":/app/freeze "$IMG" $ARGS ; then
        verb=PASSED
    else
        verb=FAILED
        let failed+=1
    fi
    echo "###############################################################"
    echo "#"
    echo "# ${verb}: ${PY_VERSION} with constraints '$ARGS'"
    echo "${verb} constraints='$ARGS'" >> "${summfile}"
    echo "#"
    echo "###############################################################"
    echo
done

sort "${summfile}"
num_tested_configs=$(ls "${pip_freeze_dir}" | wc -l)
echo "Number of configs tested (ignoring duplicates): ${num_tested_configs}"

rm -rf "${constfile}" "${summfile}" "${pip_freeze_dir}" || true

if [[ $total == 0 ]]; then
    echo "ERROR: No tests performed (this should never happen)" 1>&2
    exit 2
elif [[ $failed != 0 ]]; then
    echo "ERROR: $failed tests passed (out of $total total)"
    exit 1
fi

echo "All $total tests passed"
exit 0
