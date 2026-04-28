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
from contextlib import AbstractContextManager
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import multiprocessing
import socket
import ssl
import time
from types import TracebackType
# Because we wish to support Python versions back to 3.6, we
# import Type and Union, rather than using type or |
from typing import (
    ClassVar,
    Type,
    Union
)
from urllib.parse import parse_qs, urlparse

from .defs import (DROP_SC,
                   ProtocolType,
                   ReqCountDict,
                   ReqCountKey,
                   ReqMethodName,
                   ReqParams,
                   SERVER_HOSTNAME,
                   SingleProtocol,
                   SINGLE_PROTOCOLS)


class MyHandler(BaseHTTPRequestHandler):
    # Using int as the factory function means that all values will
    # default to 0
    _req_count: ClassVar[ReqCountDict] = defaultdict(int)

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
            if k == "delays":
                expected_type = float
            else:
                assert k == "scs"
                expected_type = int
            try:
                params[k] = tuple(( expected_type(v_item) for v_item in v ))
            except (ValueError, TypeError) as err:
                self._send(400, f"Parameter '{k}' has an invalid value: {type(err).__name__}: {err}")
                return None
        for k in ReqParams.__annotations__:
            if k not in params:
                self._send(400, f"Missing required parameter '{k}'")
                return None
        num_delays = len(params["delays"])
        num_scs = len(params["scs"])
        if num_delays != num_scs:
            self._send(400, f"Number of delays {num_delays} != number of scs {num_scs}")
            return None
        try:
            return ReqParams(**params)
        except (ValueError, TypeError) as e:
            self._send(400, f"{type(e).__name__}: {e}")
            return None

    def _send(self, sc: int, msg: str = None) -> None:
        try:
            self.send_response(sc)
        except BrokenPipeError:
            logging.debug("BrokenPipeError in send_response(%d) (likely client disconnect)",
                          sc)
            return
        try:
            self.end_headers()
        except BrokenPipeError:
            logging.debug("BrokenPipeError in end_headers() (likely client disconnect)")
            return
        if sc == 200:
            prefix = "OK"
        else:
            prefix = f"Custom {sc} error"
        if msg is None:
            msg = prefix
        else:
            msg = f"{prefix}: {msg}"
        try:
            self.wfile.write(msg.encode())
        except BrokenPipeError:
            logging.debug("BrokenPipeError in wfile.write(%s) (likely client disconnect)",
                          msg)

    def _actually_do_method(self, method: ReqMethodName, params: ReqParams) -> None:
        req_key: ReqCountKey = (method, params)
        current_count: int = min(self._req_count[req_key], len(params.scs)-1)
        self._req_count[req_key] += 1

        sc = params.scs[current_count]
        delay = params.delays[current_count]
        # If a delay is specified, first wait
        if delay:
            logging.debug("_do_method: method=%s params=%s sc=%d: Sleeping %f",
                          method, params, sc, delay)
            time.sleep(delay)
            logging.debug("_do_method: method=%s params=%s sc=%d: Done sleeping %f",
                          method, params, sc, delay)

        # Only send a response if sc is not DROP_SC
        if sc != DROP_SC:
            self._send(sc)

        return

    def _do_method(self, method: ReqMethodName) -> None:
        """
        The method of handling _req_count is not thread-safe, but this is okay,
        because the current implementation of the web server handles requests
        serially.
        """
        params = self._extract_params_from_query()
        if params is None:
            return
        return self._actually_do_method(method, params)

    def do_GET(self) -> None:
        self._do_method("GET")

    def do_POST(self) -> None:
        self._do_method("POST")

def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))  # 0 tells the OS to pick an available port
        return s.getsockname()[1]

def run_server(stop_event: multiprocessing.Event, port: int, https: bool) -> None:
    """Run a simple HTTP server until stop_event is set."""
    proto = 'https' if https else 'http'
    httpd = HTTPServer((SERVER_HOSTNAME, port), MyHandler)
    httpd.timeout = 1  # allows periodic checks of stop_event
    if https:
        # Create an ad-hoc self-signed certificate automatically
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_default_certs()
        context = ssl._create_unverified_context()  # allows insecure cert
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    logging.debug("Server running on %s://%s:%d", proto, SERVER_HOSTNAME, port)
    while not stop_event.is_set():
        httpd.handle_request()
    logging.debug("Stop signal received; %s://%s:%d server shutting down",
                  proto, SERVER_HOSTNAME, port)

class BackgroundServer(AbstractContextManager):
    def __init__(self, proto: SingleProtocol) -> None:
        assert proto in SINGLE_PROTOCOLS
        self._proto: SingleProtocol = proto
        self._stop_event: Union[multiprocessing.Event, None] = None
        self._server_process: Union[multiprocessing.Process, None] = None
        self._port: Union[int, None] = None

    @property
    def url(self) -> str:
        assert self._port is not None
        return f"{self._proto}://{SERVER_HOSTNAME}:{self._port}/"

    @property
    def _https(self) -> bool:
        return self._proto == "https"

    def __enter__(self):
        self._stop_event = multiprocessing.Event()
        # Start server
        self._port = get_free_port()
        logging.debug("Start background server: %s", self.url)
        self._server_process = multiprocessing.Process(
                                target=run_server,
                                kwargs={
                                    "stop_event": self._stop_event,
                                    "port": self._port,
                                    "https": self._https}
        )
        self._server_process.start()

        # Give it a moment to start up
        time.sleep(0.01)
        logging.debug("Started background server: %s", self.url)
        return self.url

    def __exit__(  # pylint: disable=useless-return
            self, exc_type: Union[Type[BaseException], None],
            exc_val: Union[BaseException, None],
            exc_tb: Union[TracebackType, None]) -> Union[bool, None]:
        (url,
         stop_event,
         server_process,
         self._stop_event,
         self._port,
         self._server_process) = (self.url,
                                  self._stop_event,
                                  self._server_process,
                                  None, None, None)
        logging.debug("Stopping background server %s", url)
        stop_event.set()
        server_process.join()
        logging.debug("Stopped background server %s", url)
        return None
