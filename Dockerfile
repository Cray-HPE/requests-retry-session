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
ARG ALPINE_BASE_IMAGE=artifactory.algol60.net/csm-docker/stable/docker.io/library/alpine:3.22
RG PY_VERSION=3.13
ARG PYBIN=python$PY_VERSION
ARG BASE_IMAGE_VERSION=$PY_VERSION
ARG PIP_CACHE_DIR=/app/pip-cache
ARG PIP_DL_DIR=/app/pip-dl
ARG SKIP_RC=57
ARG SSL_DIR=/app/ssl
ARG KEYFILE_NAME=key.pem
ARG CERTFILE_NAME=key.pem
ARG KEYFILE=${SSL_DIR}/${KEYFILE_NAME}
ARG CERTFILE=${SSL_DIR}/${CERTFILE_NAME}

from $ALPINE_BASE_IMAGE as openssl
ARG SSL_DIR
ARG KEYFILE
ARG CERTFILE
WORKDIR /app
RUN --mount=type=secret,id=netrc,target=/root/.netrc \
    apk add --no-cache openssl-dev && \
    apk -U upgrade --no-cache && \
    mkdir -p "${SSL_DIR}" && \
    openssl req -x509 \
                -newkey rsa:2048 \
                -keyout "${KEYFILE}" \
                -out "${CERTFILE}" \
                -days 365 \
                -nodes

FROM $BASE_IMAGE_NAME:$BASE_IMAGE_VERSION
ARG PYBIN
ARG PY_VERSION
ARG PIP_CACHE_DIR
ARG PIP_DL_DIR
ARG SKIP_RC
ARG SSL_DIR
ARG KEYFILE
ARG CERTFILE
ENV KEYFILE=${KEYFILE}
ENV CERTFILE=${CERTFILE}
ENV PY_VERSION=${PY_VERSION}
ENV PIP_CACHE_DIR="${PIP_CACHE_DIR}"
ENV PIP_DL_DIR="${PIP_DL_DIR}"
ENV SKIP_RC=${SKIP_RC}
WORKDIR /app
COPY --from=openssl "${SSL_DIR}/" "${SSL_DIR}"
COPY test_rrs/ /app/test_rrs
COPY cache_pip.sh \
     gen_test_constraints.py \
     requests_retry_session*.whl \
     test_rrs.sh \
     test_constraint_combinations.dat \
     validate_skip_rc.sh /app/
RUN chmod +rx /app/test_rrs.sh /app/cache_pip.sh /app/validate_skip_rc.sh && \
    mkdir -p "${PIP_CACHE_DIR}" "${PIP_DL_DIR}" && \
    "${PYBIN}" -m venv /app/venv && \
    /app/venv/bin/pip3 install --no-cache-dir -U pip && \
    /app/venv/bin/pip3 list --format freeze && \
    /app/cache_pip.sh && \
    /app/venv/bin/pip3 list --format freeze && \
    ls "${PIP_DL_DIR}" && \
    chmod -R a+rwx "${PIP_CACHE_DIR}" "${PIP_DL_DIR}"

ENTRYPOINT ["/app/test_rrs.sh"]
