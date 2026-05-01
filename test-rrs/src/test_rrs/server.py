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

from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import AbstractContextManager, ExitStack
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import multiprocessing
from multiprocessing.synchronize import Event
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

from .certs import CertFiles
from .defs import (
    CertFilePaths,
    DROP_SC,
    ReqCountDict,
    ReqCountKey,
    ReqMethodName,
    ReqParamDelays,
    ReqParamId,
    ReqParamScs,
    ReqParams,
    SERVER_HOSTNAME
)


class MyHandler(BaseHTTPRequestHandler):
    """
    Simple HTTP request handler for our testing
    """
    # Using int as the factory function means that all values will
    # default to 0
    _req_count: ClassVar[ReqCountDict] = defaultdict(int)

    def _extract_params_from_query(self) -> Union[None, ReqParams]:
        """
        Return the request parameters, or None if there is an error
        """
        query = urlparse(self.path).query
        id_param: Union[ReqParamId, None] = None
        delays_param: Union[ReqParamDelays, None] = None
        scs_param: Union[ReqParamScs, None] = None

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
                id_param = str(v[0])
                continue
            try:
                if k == "delays":
                    delays_param = tuple((float(v_item) for v_item in v))
                else:
                    assert k == "scs"
                    scs_param = tuple((int(v_item) for v_item in v))
            except (ValueError, TypeError) as err:
                self._send(400, f"Parameter '{k}' has an invalid value '{v}': {type(err).__name__}: {err}")
                return None
        if id_param is None:
            self._send(400, "Missing required parameter 'id'")
            return None
        if delays_param is None:
            self._send(400, "Missing required parameter 'delays'")
            return None
        if scs_param is None:
            self._send(400, "Missing required parameter 'scs'")
            return None
        num_delays = len(delays_param)
        num_scs = len(scs_param)
        if num_delays != num_scs:
            self._send(400, f"Number of delays {num_delays} != number of scs {num_scs}")
            return None
        try:
            return ReqParams(id=id_param, delays=delays_param, scs=scs_param)
        except (ValueError, TypeError) as e:
            self._send(400, f"{type(e).__name__}: {e}")
            # While this return statement is not necessary from an execution standpoint,
            # I think it helps communicate explicitly that the intention for this code
            # path is to stop and return None
            return None  # pylint: disable=useless-return

    def _send(self, sc: int, msg: Union[str, None] = None) -> None:
        """
        Send a response with the specified status code and (optional) message
        """
        try:
            self.send_response(sc)
        except (BrokenPipeError, ConnectionResetError) as err:
            logging.debug("%s in send_response(%d) (likely client disconnect): %s",
                          type(err).__name__, sc, err)
            return
        try:
            self.end_headers()
        except (BrokenPipeError, ConnectionResetError) as err:
            logging.debug("%s in end_headers() (likely client disconnect): %s",
                          type(err).__name__, err)
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
        except (BrokenPipeError, ConnectionResetError) as err:
            logging.debug("%s in wfile.write(%s) (likely client disconnect): %s",
                          type(err).__name__, msg, err)

    def _actually_do_method(self, method: ReqMethodName, params: ReqParams) -> None:
        """
        Parse the parameters and respond as appropriate
        """
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

    def _do_method(self, method: ReqMethodName) -> None:
        """
        The method of handling _req_count is not thread-safe, but this is okay,
        because the current implementation of the web server handles requests
        serially.
        """
        params = self._extract_params_from_query()
        if params is not None:
            self._actually_do_method(method, params)

    def do_GET(self) -> None:
        """
        GET request handler
        """
        self._do_method("GET")

    def do_POST(self) -> None:
        """
        POST request handler
        """
        self._do_method("POST")


def get_free_port() -> int:
    """
    Return the number of a free port on the system
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))  # 0 tells the OS to pick an available port
        port = s.getsockname()[1]
        assert isinstance(port, int)
        return port


def run_server(
    stop_event: Event,
    port: int,
    certs: Union[CertFilePaths, None]
) -> None:
    """Run a simple HTTP server until stop_event is set."""
    proto = 'http' if certs is None else 'https'
    httpd = HTTPServer((SERVER_HOSTNAME, port), MyHandler)
    httpd.timeout = 1  # allows periodic checks of stop_event
    if certs is not None:
        # Create an ad-hoc self-signed certificate automatically
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_default_certs()
        context.load_cert_chain(certfile=certs.cert_file,
                                keyfile=certs.key_file)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    logging.debug("Server running on %s://%s:%d", proto, SERVER_HOSTNAME, port)
    while not stop_event.is_set():
        httpd.handle_request()
    logging.debug("Stop signal received; %s://%s:%d server shutting down",
                  proto, SERVER_HOSTNAME, port)


class BackgroundServerBase(AbstractContextManager, ABC):
    """
    Base class for context manager for a background HTTP/HTTPS server process
    """
    def __init__(self) -> None:
        self._stop_event: Union[Event, None] = None
        self._server_process: Union[multiprocessing.Process, None] = None
        self._port: Union[int, None] = None

    @abstractmethod
    def _proto(self) -> str:
        """
        Returns the server protocol
        """

    def _certs(self) -> Union[CertFilePaths, None]:
        """
        Return the certificate files for the server,
        if any
        """
        return None

    @property
    def url(self) -> str:
        """
        Return the URL of the background server
        """
        assert self._port is not None
        return f"{self._proto()}://{SERVER_HOSTNAME}:{self._port}/"

    def __enter__(self) -> str:
        self._stop_event = multiprocessing.Event()
        # Start server
        self._port = get_free_port()
        logging.debug("Start background server: %s", self.url)
        self._server_process = multiprocessing.Process(
                                target=run_server,
                                kwargs={
                                    "stop_event": self._stop_event,
                                    "port": self._port,
                                    "certs": self._certs()}
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
        assert stop_event is not None
        assert server_process is not None
        logging.debug("Stopping background server %s", url)
        stop_event.set()
        logging.debug("Waiting for background server %s to stop", url)
        server_process.join()
        logging.debug("Stopped background server %s", url)
        return None


class HttpBackgroundServer(BackgroundServerBase):
    """ Background HTTP server """
    def _proto(self) -> str:
        """
        Returns the server protocol
        """
        return "http"


class HttpsBackgroundServer(BackgroundServerBase):
    """
    Context manager for the background HTTPS server process
    """
    def __init__(self) -> None:
        super().__init__()
        self._cert_files: Union[CertFilePaths, None] = None
        self._stack: ExitStack = ExitStack()

    def _proto(self) -> str:
        """
        Returns the server protocol
        """
        return "https"

    def _certs(self) -> Union[CertFilePaths, None]:
        """
        Return the certificate files for the server,
        if any
        """
        return self._cert_files

    def __enter__(self) -> str:
        self._stack.__enter__()
        self._cert_files = self._stack.enter_context(CertFiles())
        return super().__enter__()

    def __exit__(  # pylint: disable=useless-return
            self, exc_type: Union[Type[BaseException], None],
            exc_val: Union[BaseException, None],
            exc_tb: Union[TracebackType, None]) -> Union[bool, None]:
        super().__exit__(exc_type, exc_val, exc_tb)
        self._cert_files = None
        return self._stack.__exit__(exc_type, exc_val, exc_tb)
