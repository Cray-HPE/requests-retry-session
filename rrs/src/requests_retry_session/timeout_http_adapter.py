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
TimeoutHTTPAdapter class
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from requests.adapters import HTTPAdapter

from .utils import NotPassed, NOT_PASSED

if TYPE_CHECKING:
    from typing import Mapping, TypedDict

    from requests import PreparedRequest, Response
    from urllib3 import Retry

    # To simplify type hints
    type BytesOrStringType = bytes | str
    type TimeoutType = float | tuple[float, float] | tuple[float, None] | None
    type VerifyType = bool | str
    type CertType = BytesOrStringType | tuple[BytesOrStringType,
                                              BytesOrStringType] | None
    type ProxiesType = Mapping[str, str] | None

    class _SendArgs(TypedDict, total=False):
        """
        The valid kwargs for HTTPAdapter.send()
        """
        stream: bool
        timeout: TimeoutType
        verify: VerifyType
        cert: CertType
        proxies: ProxiesType

    class _InitArgs(TypedDict, total=False):
        """
        The valid kwargs for HTTPAdapter.__init__()
        """
        pool_connections: int
        pool_maxsize: int
        max_retries: Retry | int | None
        pool_block: bool


class TimeoutHTTPAdapter(HTTPAdapter):
    """
    An HTTP Adapter that allows a session level timeout for both read and connect attributes.
    This prevents interruption to reads that happen as a function of time or istio resets that
    causes our applications to sit and wait forever on a half open socket.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
            self,
            pool_connections: int | NotPassed = NOT_PASSED,
            pool_maxsize: int | NotPassed = NOT_PASSED,
            max_retries: Retry | int | None | NotPassed = NOT_PASSED,
            pool_block: bool | NotPassed = NOT_PASSED,
            timeout: TimeoutType = None) -> None:
        self.timeout: TimeoutType = timeout
        kwargs: _InitArgs = {}
        if not isinstance(pool_connections, NotPassed):
            kwargs["pool_connections"] = pool_connections
        if not isinstance(pool_maxsize, NotPassed):
            kwargs["pool_maxsize"] = pool_maxsize
        if not isinstance(max_retries, NotPassed):
            kwargs["max_retries"] = max_retries
        if not isinstance(pool_block, NotPassed):
            kwargs["pool_block"] = pool_block
        super().__init__(**kwargs)

    def send(  # pylint: disable=too-many-arguments,too-many-positional-arguments
            self,
            request: PreparedRequest,
            stream: bool | NotPassed = NOT_PASSED,
            timeout: TimeoutType = None,
            verify: VerifyType | NotPassed = NOT_PASSED,
            cert: CertType | NotPassed = NOT_PASSED,
            proxies: ProxiesType | NotPassed = NOT_PASSED) -> Response:
        kwargs: _SendArgs = {
            "timeout":
            self.timeout if timeout is None else timeout
        }
        if not isinstance(stream, NotPassed):
            kwargs["stream"] = stream
        if not isinstance(verify, NotPassed):
            kwargs["verify"] = verify
        if not isinstance(cert, NotPassed):
            kwargs["cert"] = cert
        if not isinstance(proxies, NotPassed):
            kwargs["proxies"] = proxies
        return super().send(request, **kwargs)
