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

set -uo pipefail

IMG="pytest-${PY_VERSION}:${DOCKER_VERSION}"

ARGS=()

if [[ $PY_VERSION == 3.6 ]]; then
    function add_args
    {
        ARGS+=( "$*" )
    }
else
    function add_args
    {
        ARGS+=( "$*" "$* typing_extensions==4.7" )
    }
fi

add_args ""

while IFS= read -r line; do
    # Skip comment lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    # Skip completely empty lines
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue

    # Split into three fields using | as delimiter
    IFS='|' read -r f1 f2 f3 <<< "$line"

    skip=y
    for py in $f1; do
        [[ $py == all || $py == ${PY_VERSION} ]] && skip=n && break
    done
    [[ $skip == y ]] && continue

    # Strip leading/trailing whitespace from each field
    c1="$(echo "$f2" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
    c2="$(echo "$f3" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"

    [[ -n $c1 ]] && add_args "$c1" && [[ -n $c2 ]] && add_args "$c1 $c2"
    [[ -n $c2 ]] && add_args "$c2"
done < constraints.dat

for A in "${ARGS[@]}"; do
    # Deliberately do not quote $A, so it is split into multiple arguments
    # if there is whitespace in it, or it will not be an argument at all,
    # if it is empty
    docker run "$IMG" $A || exit 1
done

exit 0
