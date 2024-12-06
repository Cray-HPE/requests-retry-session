#
# MIT License
#
# (C) Copyright 2022-2024 Hewlett Packard Enterprise Development LP
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
    from typing import Mapping, TypedDict, Union
    from requests import PreparedRequest, Response

    # To simplify type hints
    BytesOrStringType = Union[bytes, str]
    TimeoutType = Union[float, tuple[float, float], tuple[float, None], None]
    VerifyType = Union[bool, str]
    CertType = Union[BytesOrStringType, tuple[BytesOrStringType,
                                              BytesOrStringType], None]
    ProxiesType = Union[Mapping[str, str], None]

    class _SendArgs(TypedDict, total=False):  # pylint: disable=missing-class-docstring
        stream: bool
        timeout: TimeoutType
        verify: VerifyType
        cert: CertType
        proxies: ProxiesType


class _NotPassed:  # pylint: disable=missing-class-docstring,too-few-public-methods
    pass


_NOT_PASSED = _NotPassed()


class TimeoutHTTPAdapter(HTTPAdapter):
    """
    An HTTP Adapter that allows a session level timeout for both read and connect attributes.
    This prevents interruption to reads that happen as a function of time or istio resets that
    causes our applications to sit and wait forever on a half open socket.
    """

    def __init__(self,
                 *args,
                 timeout: TimeoutType = None,
                 **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.timeout: TimeoutType = timeout
        super().__init__(*args, **kwargs)

    def send(
        self,
        request: PreparedRequest,
        stream: Union[bool, _NotPassed] = _NOT_PASSED,
        timeout: Union[TimeoutType, _NotPassed] = _NOT_PASSED,
        verify: Union[VerifyType, _NotPassed] = _NOT_PASSED,
        cert: Union[CertType, _NotPassed] = _NOT_PASSED,
        proxies: Union[ProxiesType, _NotPassed] = _NOT_PASSED
    ) -> Response:  # pylint: disable=too-many-arguments,too-many-positional-arguments
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
