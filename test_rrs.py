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

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
from typing import Iterator, Optional

import requests

import requests_retry_session as rrs

PROTOCOL = 'http'
PORT=8000
URL=f"{PROTOCOL}://localhost:{PORT}"

GOOD_URI="/rc/200"
BAD_URI="/rc/520"
ONCE_521_URI="/once/521/rc/200"
ONCE_522_URI="/once/522/rc/200"

GOOD_URL=f"{URL}{GOOD_URI}"
BAD_URL=f"{URL}{BAD_URI}"
ONCE_521_URL=f"{URL}{ONCE_521_URI}"
ONCE_522_URL=f"{URL}{ONCE_522_URI}"

DEFAULT_RETRY_ADAPTER_ARGS = rrs.RequestsRetryAdapterArgs(
    retries=2,
    backoff_factor=0.05,
    status_forcelist=(521, 522),
    connect_timeout=2,
    read_timeout=2)

SENT_SC = { 521: False, 522: False }

class MyHandler(BaseHTTPRequestHandler):
    def _send_ok(self) -> None:
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def _send_err(self, sc: int) -> None:
        self.send_response(sc)
        self.end_headers()
        self.wfile.write(b"Custom %d error" % sc)

    def do_GET(self) -> None:
        if self.path == GOOD_URI:
            self._send_ok()
            return

        if self.path == BAD_URI:
            self._send_err(520)
            return

        if self.path == ONCE_521_URI:
            if SENT_SC[521]:
                self._send_ok()
            else:
                self._send_err(521)
                SENT_SC[521]=True
            return

        if self.path == ONCE_522_URI:
            if SENT_SC[522]:
                self._send_ok()
            else:
                self._send_err(522)
                SENT_SC[522]=True               
            return

        self._send_err(550)

def print_err(s) -> None:
    sys.stderr.write(f"ERROR: {s}\n")
    sys.stderr.flush()

def retry_session_manager():
    return rrs.retry_session_manager(protocol=PROTOCOL,
                                     **DEFAULT_RETRY_ADAPTER_ARGS)

def retry_session(
    protocol: Optional[str] = None,
    adapter_kwargs: Optional[rrs.RequestsRetryAdapterArgs] = None
) -> Iterator[requests.Session]:
    kwargs = adapter_kwargs or {}
    if protocol is not None:
        return retry_session_manager(protocol=protocol, **kwargs)  # pylint: disable=redundant-keyword-arg
    return retry_session_manager(**kwargs)


def retry_session_get(*get_args,
                      protocol: Optional[str] = None,
                      adapter_kwargs: Optional[
                          rrs.RequestsRetryAdapterArgs] = None,
                      **get_kwargs) -> Iterator[requests.Response]:
    with retry_session(protocol=protocol,
                       adapter_kwargs=adapter_kwargs) as _session:
        return _session.get(*get_args, **get_kwargs)


def start_server(server: HTTPServer) -> None:
    server.serve_forever()


def non_cm_get(url: str, expected_sc: int) -> bool:
    msg_pre=f"Non-CM GET to {url}"
    msg_post=f"(expected status code {expected_sc})"
    print(f"{msg_pre} {msg_post}")
    try:
        sc = rrs.requests_retry_session(protocol=PROTOCOL, **DEFAULT_RETRY_ADAPTER_ARGS).get(url).status_code
        msg = f"{msg_pre} returned status code {sc} {msg_post}"
        if sc == expected_sc:
            print(msg)
            return True
        print_err(msg)
    except Exception as err:
        print_err(f"{msg_pre} raised {type(err).__name__}: {err} {msg_post}")
    return False

def cm_get(url: str, expected_sc: int) -> bool:
    msg_pre=f"CM GET to {url}"
    msg_post=f"(expected status code {expected_sc})"
    print(f"{msg_pre} {msg_post}")
    try:
        sc = retry_session_get(url).status_code
        msg = f"{msg_pre} returned status code {sc} {msg_post}"
        if sc == expected_sc:
            print(msg)
            return True
        print_err(msg)
    except Exception as err:
        print_err(f"{msg_pre} raised {type(err).__name__}: {err} {msg_post}")
    return False

def main() -> int:
    exit_rc = 0
    print("Start background {PROTOCOL} server on localhost:{PORT}")
    server = HTTPServer(("localhost", PORT), MyHandler)
    thread = threading.Thread(target=start_server, kwargs={"server":server}, daemon=True)
    thread.start()

    if not non_cm_get(GOOD_URL, 200):
        exit_rc = 1
    if not cm_get(GOOD_URL, 200):
        exit_rc = 1
    if not non_cm_get(BAD_URL, 520):
        exit_rc = 1
    if not cm_get(BAD_URL, 520):
        exit_rc = 1
    if not non_cm_get(ONCE_521_URL, 200):
        exit_rc = 1
    if not cm_get(ONCE_522_URL, 200):
        exit_rc = 1

    print(f"Stopping {PROTOCOL} server")
    server.shutdown()
    thread.join()
    print(f"{PROTOCOL} server stopped")
    return exit_rc


if __name__ == '__main__':
    sys.exit(main())
