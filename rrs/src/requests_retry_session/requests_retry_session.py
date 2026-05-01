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

import sys
from typing import Optional

if sys.version_info >= (3, 9):
    from collections.abc import Collection
    from typing import TypedDict
else:
    from typing import Collection
    from typing_extensions import TypedDict

import requests

from .retry_with_logs import RetryWithLogs
from .timeout_http_adapter import TimeoutHTTPAdapter
from .utils import NotPassed, NOT_PASSED


DEFAULT_BACKOFF_FACTOR = 0.5
DEFAULT_CONNECT_TIMEOUT = 3
# Protocols should omit the trailing "://" because it will be automatically appended
DEFAULT_PROTOCOL = 'http'
DEFAULT_READ_TIMEOUT = 10
DEFAULT_RETRIES = 10
DEFAULT_STATUS_FORCELIST = (500, 502, 503, 504)


class RequestsRetryAdapterArgs(TypedDict, total=False):
    """
    Used to represent the parameters to the requests_retry_adapter function.
    Helpful with type hinting.
    """
    retries: int
    backoff_factor: float
    status_forcelist: Collection[int]
    allowed_methods: Collection[str]
    connect_timeout: float
    read_timeout: float


def requests_session(adapter,
                     session = None,
                     protocol = DEFAULT_PROTOCOL):
    """
    Protocols should omit the trailing "://" because it will be automatically appended

    adapter: requests.adapters.HTTPAdapter,
    session: Optional[requests.Session]
    protocol: Union[str, Iterable[str]]
    -> requests.Session:
    """
    if isinstance(protocol, str):
        return requests_session(adapter=adapter, session=session, protocol=[protocol])
    session = session or requests.Session()
    for proto in protocol:
        # Must mount to <proto>://
        # Mounting to only <proto> will not work!
        session.mount(f"{proto}://", adapter)
    return session


def requests_retry_adapter(  # pylint: disable=too-many-positional-arguments
        retries = DEFAULT_RETRIES,
        backoff_factor = DEFAULT_BACKOFF_FACTOR,
        status_forcelist = DEFAULT_STATUS_FORCELIST,
        connect_timeout = DEFAULT_CONNECT_TIMEOUT,
        read_timeout = DEFAULT_READ_TIMEOUT,
        allowed_methods = NOT_PASSED
):
    """
    retries: int
    backoff_factor: float
    status_forcelist: Collection[int]
    connect_timeout: float
    read_timeout: float
    allowed_methods: Union[Collection[str], NotPassed]
    -> .timeout_http_adapter.TimeoutHTTPAdapter:

    Return a TimeoutHTTPAdapter based on the specified arguments
    """
    retry_kwargs = {
        "total": retries,
        "read": retries,
        "connect": retries,
        "backoff_factor": backoff_factor,
        "status_forcelist": status_forcelist}
    if not isinstance(allowed_methods, NotPassed):
        retry_kwargs["allowed_methods"] = allowed_methods
    retry = RetryWithLogs(**retry_kwargs)
    return TimeoutHTTPAdapter(max_retries=retry,
                              timeout=(connect_timeout, read_timeout))


def requests_retry_session(
        session = None,
        protocol = DEFAULT_PROTOCOL,
        **adapter_kwargs
):
    """
    Protocols should omit the trailing "://" because it will be automatically appended later

    session: Optional[requests.Session]
    protocol: Union[str, Iterable[str]]
    **adapter_kwargs: Unpack[RequestsRetryAdapterArgs]
    -> requests.Session
    """
    adapter = requests_retry_adapter(**adapter_kwargs)
    return requests_session(adapter=adapter,
                            session=session,
                            protocol=protocol)
