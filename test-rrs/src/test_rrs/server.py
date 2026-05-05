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
from contextlib import AbstractContextManager, ExitStack
from http.server import HTTPServer
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
    Type,
    Union
)

from .certs import CertFiles
from .defs import (
    CertFilePaths,
    SERVER_HOSTNAME
)
from .test_http_handler import TestHttpHandler


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
    httpd = HTTPServer((SERVER_HOSTNAME, port), TestHttpHandler)
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
