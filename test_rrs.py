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

"""
Minimal RRS module test, mainly to ensure that it is not completely broken.
"""

from collections import defaultdict
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
from typing import Dict

import requests_retry_session as rrs

PROTOCOL = 'http'
PORT=8000
URL=f"{PROTOCOL}://localhost:{PORT}"

GOOD_URI="/rc/200"
BAD_URI="/rc/520"
ONCE_521_URI="/once/521/rc/200"
ONCE_522_URI="/once/522/rc/200"
ONCE_523_URI="/once/523/rc/200"

GOOD_URL=f"{URL}{GOOD_URI}"
BAD_URL=f"{URL}{BAD_URI}"
ONCE_521_URL=f"{URL}{ONCE_521_URI}"
ONCE_522_URL=f"{URL}{ONCE_522_URI}"
ONCE_523_URL=f"{URL}{ONCE_523_URI}"

DEFAULT_RETRY_ADAPTER_ARGS = rrs.RequestsRetryAdapterArgs(
    retries=2,
    backoff_factor=0.05,
    status_forcelist=(521, 522, 523),
    connect_timeout=2,
    read_timeout=2)

# Using bool as the factory function means that all values will
# default to False
SENT_SC: Dict[int, bool] = defaultdict(bool)

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

        if self.path == ONCE_523_URI:
            if SENT_SC[523]:
                self._send_ok()
            else:
                self._send_err(523)
                SENT_SC[523]=True               
            return

        self._send_err(550)

class MyRRSessionManager(rrs.RetrySessionManager):
    """
    As a subclass of RetrySessionManager, this class can be used as a context manager,
    and will have a requests session available as self.requests_session
    """
    def __init__(self) -> None:
        super().__init__(protocol=PROTOCOL, **DEFAULT_RETRY_ADAPTER_ARGS)

def print_err(s) -> None:
    sys.stderr.write(f"ERROR: {s}\n")
    sys.stderr.flush()

def retry_session_manager():
    return rrs.retry_session_manager(protocol=PROTOCOL, **DEFAULT_RETRY_ADAPTER_ARGS)

def requests_retry_session():
    return rrs.requests_retry_session(protocol=PROTOCOL, **DEFAULT_RETRY_ADAPTER_ARGS)

def start_server(server: HTTPServer) -> None:
    server.serve_forever()

def test_get(session, session_desc: str, url: str, expected_sc: int) -> int:
    msg_pre=f"{session_desc} GET to {url}"
    msg_post=f"(expected status code {expected_sc})"
    print(f"{msg_pre} {msg_post}")
    try:
        sc = session.get(url).status_code
        msg = f"{msg_pre} returned status code {sc} {msg_post}"
        if sc == expected_sc:
            print(msg)
            return 0
        print_err(msg)
    except Exception as err:
        print_err(f"{msg_pre} raised {type(err).__name__}: {err} {msg_post}")
    return 1


def run_tests(non_cm_session, cm_func_session, cm_class_session) -> int:
    exit_rc = 0
    for sfunc, sdesc, once_url in [
        (non_cm_session, "rrs.requests_retry_session", ONCE_521_URL),
        (cm_func_session, "rrs.retry_session_manager", ONCE_522_URL),
        (cm_class_session, "rrs.RetrySessionManager", ONCE_523_URL)
    ]:
        exit_rc += test_get(sfunc, sdesc, GOOD_URL, 200)
        exit_rc += test_get(sfunc, sdesc, BAD_URL, 520)
        exit_rc += test_get(sfunc, sdesc, once_url, 200)

    return exit_rc

def main() -> int:
    print("Start background {PROTOCOL} server on localhost:{PORT}")
    server = HTTPServer(("localhost", PORT), MyHandler)
    thread = threading.Thread(target=start_server, kwargs={"server":server}, daemon=True)
    thread.start()

    print("Creating RRS session using rrs.requests_retry_session")
    non_cm_session = requests_retry_session()
    print("Creating RRS session using rrs.retry_session_manager")
    with retry_session_manager() as cm_func_session:
        print("Creating RRS session using rrs.RetrySessionManager")
        with MyRRSessionManager() as my_mgr:
            cm_class_session=my_mgr.requests_session
            print("Running tests")
            exit_rc = run_tests(non_cm_session=non_cm_session,
                                cm_func_session=cm_func_session,
                                cm_class_session=cm_class_session)

    print(f"Stopping {PROTOCOL} server")
    server.shutdown()
    thread.join()
    print(f"{PROTOCOL} server stopped")
    return exit_rc


if __name__ == '__main__':
    sys.exit(main())
