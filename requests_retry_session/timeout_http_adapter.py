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

from requests.adapters import HTTPAdapter

from .utils import NotPassed, NOT_PASSED


class TimeoutHTTPAdapter(HTTPAdapter):
    """
    An HTTP Adapter that allows a session level timeout for both read and connect attributes.
    This prevents interruption to reads that happen as a function of time or istio resets that
    causes our applications to sit and wait forever on a half open socket.
    """

    def __init__(
            self,
            pool_connections = NOT_PASSED,
            pool_maxsize = NOT_PASSED,
            max_retries = NOT_PASSED,
            pool_block = NOT_PASSED,
            timeout = None):
        """
        pool_connections: Union[int, NotPassed]
        pool_maxsize: Union[int, NotPassed]
        max_retries: Union[Retry, int, None, NotPassed]
        pool_block: Union[bool, NotPassed]
        timeout: Union[float, tuple[float, float], tuple[float, None], None]
        -> None
        """
        self.timeout = timeout
        kwargs = {}
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
            request,
            stream = NOT_PASSED,
            timeout = None,
            verify = NOT_PASSED,
            cert = NOT_PASSED,
            proxies = NOT_PASSED):
        """
        request: PreparedRequest,
        stream: Union[bool, NotPassed]
        timeout: Union[float,
                       tuple[float, float],
                       tuple[float, None],
                       None]
        verify: Union[VerifyType, NotPassed]
        cert: Union[CertType, NotPassed]
        proxies: Union[ProxiesType, NotPassed]
        -> Response:
        """
        kwargs = {
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
