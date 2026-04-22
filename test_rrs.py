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
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import random
import string
import sys
import threading
# Because we wish to support Python versions back to 3.6, we import
# Iterable from typing rather than collections.abc
# For the same reason, we import Tuple, Type, and Union, rather
# than using tuple, type, or |
from typing import Callable, DefaultDict, Iterable, NamedTuple, Tuple, Type, Union
from urllib.parse import parse_qs, urlparse

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

import requests_retry_session as rrs

ProtocolType: TypeAlias = str
PROTOCOL: ProtocolType = 'http'
PORT=8000
URL=f"{PROTOCOL}://localhost:{PORT}/"

class ReqParams(NamedTuple):
    id: str
    scs: Tuple[int, ...]

RR_ADAPTER_ARGS = rrs.RequestsRetryAdapterArgs(
    retries=2,
    backoff_factor=0.05,
    status_forcelist=(521, 522, 523),
    connect_timeout=0.2,
    read_timeout=0.2
)

# Using int as the factory function means that all values will
# default to 0
REQ_COUNT: DefaultDict[ReqParams, int] = defaultdict(int)

class MyHandler(BaseHTTPRequestHandler):
    def _extract_params_from_query(self) -> Union[None, ReqParams]:
        query = urlparse(self.path).query
        params={}
        for k, v in parse_qs(query).items():
            if k not in ReqParams.__annotations__:
                self._send(400, f"Unknown request parameter: '{k}'")
                return None
            if not v:
                self._send(400, f"No value specified for parameter '{k}'")
                return None
            if k == "id":
                if len(v) > 1:
                    self._send(400, f"Parameter '{k}' was specified '{len(v)}' times")
                    return None
                params[k] = str(v[0])
                continue
            assert k == "scs"
            try:
                params[k] = tuple([ int(v_item) for v_item in v ])
            except (ValueError, TypeError):
                self._send(400, f"Parameter '{k}' has an invalid value '{value}'")
                return None
        try:
            return ReqParams(**params)
        except (ValueError, TypeError) as e:
            self._send(400, f"{type(e).__name__}: {e}")
            return None

    def _send(self, sc: int, msg: str = None) -> None:
        self.send_response(sc)
        self.end_headers()
        if sc == 200:
            prefix = "OK"
        else:
            prefix = f"Custom {sc} error"
        if msg is None:
            msg = prefix
        else:
            msg = f"{prefix}: {msg}"
        self.wfile.write(msg.encode())

    def do_GET(self) -> None:
        params = self._extract_params_from_query()
        if params is None:
            return
        req_key = params
        current_count = min(REQ_COUNT[req_key], len(params.scs)-1)
        REQ_COUNT[req_key] += 1

        sc = params.scs[current_count]
        # Only send a response if sc is positive
        if sc > 0:
            self._send(sc)
        return

class MyRRSessionManager(rrs.RetrySessionManager):
    """
    As a subclass of RetrySessionManager, this class can be used as a context manager,
    and will have a requests session available as self.requests_session
    """
    def __init__(self, proto: ProtocolType, adapter_args: rrs.RequestsRetryAdapterArgs) -> None:
        super().__init__(protocol=proto, **adapter_args)

def random_id() -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(16))

def prepend_timestamp(text: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    return f"{timestamp} {text}"

def print_msg(s: str) -> None:
    sys.stdout.write(prepend_timestamp(f"{s}\n"))
    sys.stderr.flush()

def print_err(s: str) -> None:
    sys.stderr.write(f"ERROR: {prepend_timestamp(s)}\n")
    sys.stderr.flush()

def start_server(server: HTTPServer) -> None:
    server.serve_forever()

def test_req(
    session_method: Callable,
    session_desc: str,
    expected_sc: Union[int, Type[Exception]],
    scs: Union[int, Iterable[int]]
) -> int:
    """
    expected_sc is either the expected status code, or the type of Exception
    we expect to be raised
    """
    req_params = { 'id': random_id(), 'scs': scs }
    msg_pre=f"{session_desc} with params={req_params}"
    if isinstance(expected_sc, int):
        msg_post=f"(expected status code {expected_sc})"
    else:
        msg_post=f"(expected to raise {expected_sc.__name__} exception)"
    print_msg(f"{msg_pre} {msg_post}")
    try:
        sc = session_method(URL, params=req_params).status_code
        msg = f"{msg_pre} returned status code {sc} {msg_post}"
        if isinstance(expected_sc, int) and sc == expected_sc:
            print_msg(msg)
            return 0
        print_err(msg)
    except Exception as err:
        msg = f"{msg_pre} raised {type(err).__name__}: {err} {msg_post}"
        if issubclass(expected_sc, Exception) and isinstance(err, expected_sc):
            print_msg(msg)
            return 0
        print_err(msg)
    return 1


def run_get_tests(
    non_cm_session: Callable,
    cm_func_session: Callable,
    cm_class_session: Callable
) -> int:
    exit_rc = 0
    for sfunc, sdesc in [
        (non_cm_session.get, "rrs.requests_retry_session GET"),
        (cm_func_session.get, "rrs.retry_session_manager GET"),
        (cm_class_session.get, "rrs.RetrySessionManager GET")
    ]:
        # With no parameters being specified, we expect a simple 200 response
        exit_rc += test_req(sfunc, sdesc, 200, scs=200)
        # Now test an endpoint that always returns 520
        exit_rc += test_req(sfunc, sdesc, 520, scs=520)
        # Now test an endpoint that initially returns 521, then returns 201
        exit_rc += test_req(sfunc, sdesc, 201, scs=[521,201])
        # Now test an endpoint that initially should time out, then returns 202
        exit_rc += test_req(sfunc, sdesc, 202, scs=[0,202])

    return exit_rc

def main() -> int:
    exit_rc = 0
    print_msg(f"Start background {PROTOCOL} server on localhost:{PORT}")
    server = HTTPServer(("localhost", PORT), MyHandler)
    thread = threading.Thread(target=start_server, kwargs={"server":server}, daemon=True)
    thread.start()

    print_msg(f"Creating RRS session using rrs.requests_retry_session")
    non_cm_session = rrs.requests_retry_session(protocol=PROTOCOL,
                                                **RR_ADAPTER_ARGS)
    print_msg(f"Creating RRS session using rrs.retry_session_manager")
    with rrs.retry_session_manager(protocol=PROTOCOL,
                                   **RR_ADAPTER_ARGS) as cm_func_session:
        print_msg(f"Creating RRS session using rrs.RetrySessionManager")
        with MyRRSessionManager(PROTOCOL, RR_ADAPTER_ARGS) as my_mgr:
            cm_class_session=my_mgr.requests_session
            print_msg("Running tests")
            exit_rc += run_get_tests(non_cm_session=non_cm_session,
                                     cm_func_session=cm_func_session,
                                     cm_class_session=cm_class_session)

    print_msg(f"Stopping {PROTOCOL} server")
    server.shutdown()
    thread.join()
    print_msg(f"{PROTOCOL} server stopped")
    return exit_rc


if __name__ == '__main__':
    sys.exit(main())
