#
# MIT License
#
# (C) Copyright 2020-2026 Hewlett Packard Enterprise Development LP
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
RetryWithLogs class
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from urllib3 import Retry

if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self
    from urllib3 import BaseHTTPResponse
    from urllib3.connectionpool import ConnectionPool

LOGGER = logging.getLogger(__name__)


class RetryWithLogs(Retry):
    """
    A urllib3.Retry adapter that allows us to modify the behavior of
    what happens during retry. By overwriting the superclassed method increment, we
    can provide the user with information about how frequently we are reattempting
    an endpoint.

    Providing this feedback to the user allows us to dramatically increase the number
    of retry operations within the provided call to an attempted upstream API, and
    gives users a chance to intervene on behalf of the slower upstream service. This
    behavior is consistent with existing retry behavior that is expected by all of our
    API interactions, as well, gives us a more immediate sense of feedback for overall
    system instability and network congestion.
    """
    def increment(self,
                  method: str | None = None,
                  url: str | None = None,
                  response: BaseHTTPResponse | None = None,
                  error: Exception | None = None,
                  _pool: ConnectionPool | None = None,
                  _stacktrace: TracebackType | None = None) -> Self:
        if _pool is None:
            raise TypeError(f"_pool argument should not be None. {locals()}")
        if url is None:
            raise TypeError(f"url argument should not be None. {locals()}")
        if method is None:
            raise TypeError(f"method argument should not be None. {locals()}")
        endpoint = f"{_pool.scheme}://{_pool.host}{url}"
        if response is None:
            LOGGER.info("Reattempting %s request for '%s'", method, endpoint)
        else:
            LOGGER.warning(
                "Previous %s attempt on '%s' resulted in %s response.", method,
                endpoint, response.status)
            LOGGER.info("Reattempting %s request for '%s'", method, endpoint)
        return super().increment(method, url, response, error, _pool,
                                 _stacktrace)
