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
from http.server import BaseHTTPRequestHandler
import logging
import time
# Because we wish to support Python versions back to 3.6, we
# import Union, rather than using |
from typing import (
    ClassVar,
    DefaultDict,
    Tuple,
    Union,
)
from urllib.parse import parse_qs, urlparse

from test_rrs.defs import (
    RequestVerb,
    ReqParamDelays,
    ReqParamId,
    ReqParamScs,
    ReqParams,
)
from test_rrs.typing_imports import TypeAlias


ReqCountKey: TypeAlias = Tuple[RequestVerb, ReqParams]
ReqCountDict: TypeAlias = DefaultDict[ReqCountKey, int]

# DROP_SC is the SC that tells the server to just disconnect without response
DROP_SC = 0


class TestHttpHandler(BaseHTTPRequestHandler):
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

    def _actually_do_method(self, method: RequestVerb, params: ReqParams) -> None:
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

    def _do_method(self, method: RequestVerb) -> None:
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
