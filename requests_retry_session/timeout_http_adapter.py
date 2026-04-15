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

from __future__ import annotations
from typing import TYPE_CHECKING

from requests.adapters import HTTPAdapter

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

class _NotPassed:  # pylint: disable=too-few-public-methods
    """
    A dummy class to let us distinguish between an argument not being passed versus
    an argument explicitly being passed with a None value
    """
    pass


_NOT_PASSED = _NotPassed()


class TimeoutHTTPAdapter(HTTPAdapter):
    """
    An HTTP Adapter that allows a session level timeout for both read and connect attributes.
    This prevents interruption to reads that happen as a function of time or istio resets that
    causes our applications to sit and wait forever on a half open socket.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
            self,
            pool_connections: int | _NotPassed = _NOT_PASSED,
            pool_maxsize: int | _NotPassed = _NOT_PASSED,
            max_retries: Retry | int | None | _NotPassed = _NOT_PASSED,
            pool_block: bool | _NotPassed = _NOT_PASSED,
            timeout: TimeoutType = None) -> None:
        self.timeout: TimeoutType = timeout
        kwargs: _InitArgs = {}
        if not isinstance(pool_connections, _NotPassed):
            kwargs["pool_connections"] = pool_connections
        if not isinstance(pool_maxsize, _NotPassed):
            kwargs["pool_maxsize"] = pool_maxsize
        if not isinstance(max_retries, _NotPassed):
            kwargs["max_retries"] = max_retries
        if not isinstance(pool_block, _NotPassed):
            kwargs["pool_block"] = pool_block
        super().__init__(**kwargs)

    def send(  # pylint: disable=too-many-arguments,too-many-positional-arguments
            self,
            request: PreparedRequest,
            stream: bool | _NotPassed = _NOT_PASSED,
            timeout: TimeoutType | _NotPassed = _NOT_PASSED,
            verify: VerifyType | _NotPassed = _NOT_PASSED,
            cert: CertType | _NotPassed = _NOT_PASSED,
            proxies: ProxiesType | _NotPassed = _NOT_PASSED) -> Response:
        kwargs: _SendArgs = {
            "timeout":
            self.timeout if isinstance(timeout, _NotPassed) else timeout
        }
        if not isinstance(stream, _NotPassed):
            kwargs["stream"] = stream
        if not isinstance(verify, _NotPassed):
            kwargs["verify"] = verify
        if not isinstance(cert, _NotPassed):
            kwargs["cert"] = cert
        if not isinstance(proxies, _NotPassed):
            kwargs["proxies"] = proxies
        return super().send(request, **kwargs)
