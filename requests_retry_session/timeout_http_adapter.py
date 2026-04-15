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

    def __init__(
            self,
            pool_connections = _NOT_PASSED,
            pool_maxsize = _NOT_PASSED,
            max_retries = _NOT_PASSED,
            pool_block = _NOT_PASSED,
            timeout = None):
        """
        pool_connections: Union[int, _NotPassed]
        pool_maxsize: Union[int, _NotPassed]
        max_retries: Union[Retry, int, None, _NotPassed]
        pool_block: Union[bool, _NotPassed]
        timeout: Union[float, tuple[float, float], tuple[float, None], None]
        -> None
        """
        self.timeout = timeout
        kwargs = {}
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
            request,
            stream = _NOT_PASSED,
            timeout = _NOT_PASSED,
            verify = _NOT_PASSED,
            cert = _NOT_PASSED,
            proxies = _NOT_PASSED):
        """
        request: PreparedRequest,
        stream: Union[bool, _NotPassed]
        timeout: Union[Union[float,
                             tuple[float, float],
                             tuple[float, None],
                             None]
                       _NotPassed]
        verify: Union[VerifyType, _NotPassed]
        cert: Union[CertType, _NotPassed]
        proxies: Union[ProxiesType, _NotPassed]
        -> Response:
        """
        kwargs = {
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
