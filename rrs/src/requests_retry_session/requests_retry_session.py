#
# MIT License
#
# (C) Copyright 2022-2026 Hewlett Packard Enterprise Development LP
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
Requests session functions and classes
"""

from typing import Tuple, TYPE_CHECKING

import requests

from .retry_with_logs import RetryWithLogs
from .timeout_http_adapter import TimeoutHTTPAdapter
from .typing_imports import TypedDict


if TYPE_CHECKING:
    from typing import Optional
    from .typing_imports import Unpack, TypeAlias


ProtocolType: "TypeAlias" = str
StatusForcelistType: "TypeAlias" = Tuple[int, ...]

DEFAULT_BACKOFF_FACTOR = 0.5
DEFAULT_CONNECT_TIMEOUT = 3
# protocol should omit the trailing "://" because it will be automatically appended
DEFAULT_PROTOCOL: "ProtocolType" = 'http'
DEFAULT_READ_TIMEOUT = 10
DEFAULT_RETRIES = 10
DEFAULT_STATUS_FORCELIST: "StatusForcelistType" = (500, 502, 503, 504)


class RequestsRetryAdapterArgs(TypedDict, total=False):
    """
    Used to represent the parameters to the requests_retry_adapter function.
    Helpful with type hinting.
    """
    retries: int
    backoff_factor: float
    status_forcelist: StatusForcelistType
    connect_timeout: float
    read_timeout: float


def requests_session(adapter: "requests.adapters.HTTPAdapter",
                     session: "Optional[requests.Session]" = None,
                     protocol: "ProtocolType" = DEFAULT_PROTOCOL) -> "requests.Session":
    """
    protocol should omit the trailing "://" because it will be automatically appended
    """
    session = session or requests.Session()
    # Must mount to http://
    # Mounting to only http will not work!
    session.mount(f"{protocol}://", adapter)
    return session


def requests_retry_adapter(  # pylint: disable=too-many-positional-arguments
        retries: "int" = DEFAULT_RETRIES,
        backoff_factor: "float" = DEFAULT_BACKOFF_FACTOR,
        status_forcelist: "StatusForcelistType" = DEFAULT_STATUS_FORCELIST,
        connect_timeout: "float" = DEFAULT_CONNECT_TIMEOUT,
        read_timeout: "float" = DEFAULT_READ_TIMEOUT
) -> "TimeoutHTTPAdapter":
    """
    Return a TimeoutHTTPAdapter based on the specified arguments
    """
    retry = RetryWithLogs(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    return TimeoutHTTPAdapter(max_retries=retry,
                              timeout=(connect_timeout, read_timeout))


def requests_retry_session(
    session: "Optional[requests.Session]" = None,
    protocol: "ProtocolType" = DEFAULT_PROTOCOL,
    **adapter_kwargs: "Unpack[RequestsRetryAdapterArgs]"
) -> "requests.Session":
    """
    protocol should omit the trailing "://" because it will be automatically appended later
    """
    adapter = requests_retry_adapter(**adapter_kwargs)
    return requests_session(adapter=adapter,
                            session=session,
                            protocol=protocol)
