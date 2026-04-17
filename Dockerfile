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

ARG BASE_IMAGE_NAME=artifactory.algol60.net/csm-docker/stable/csm-docker-sle-python
ARG PY_VERSION=3.13
ARG PYBIN=python$PY_VERSION
ARG BASE_IMAGE_VERSION=$PY_VERSION

FROM $BASE_IMAGE_NAME:$BASE_IMAGE_VERSION
ARG PYBIN
WORKDIR /app
COPY requests_retry_session*.whl test_rrs.py test_rrs.sh test_constraint_combinations.dat /app/
RUN chmod +rx /app/test_rrs.sh && \
    $PYBIN -m venv /app/venv && \
    /app/venv/bin/pip3 install --no-cache-dir -U pip && \
    /app/venv/bin/pip3 list --format freeze

ENTRYPOINT ["/app/test_rrs.sh"]
