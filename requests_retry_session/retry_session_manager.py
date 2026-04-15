#
# MIT License
#
# (C) Copyright 2024-2026 Hewlett Packard Enterprise Development LP
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
from contextlib import closing, contextmanager, AbstractContextManager
from typing import TYPE_CHECKING

import requests

from .requests_retry_session import requests_retry_adapter, requests_session, \
                                    RequestsRetryAdapterArgs, DEFAULT_PROTOCOL
from .timeout_http_adapter import TimeoutHTTPAdapter

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Iterator, Type

    from typing_extensions import Self, Unpack

    from .requests_retry_session import ProtocolType

class RetrySessionManager(AbstractContextManager):
    """
    Not intended to be useful on its own, this is a base class for classes that want to create a
    retry session only when needed, and to clean it up in their __exit__ function.
    This class is not thread safe.
    """

    def __init__(self,
                 protocol: ProtocolType | None = None,
                 **adapter_kwargs: Unpack[RequestsRetryAdapterArgs]) -> None:
        """
        If specified, protocol should omit the trailing "://" because it will be automatically appended later
        """
        self._requests_adapter: TimeoutHTTPAdapter | None = None
        self._requests_session: requests.Session | None = None
        self._requests_protocol: ProtocolType = protocol if protocol is not None else DEFAULT_PROTOCOL
        self._requests_retry_adapter_kwargs: RequestsRetryAdapterArgs = adapter_kwargs

    def __exit__(  # pylint: disable=useless-return
            self, exc_type: Type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None) -> bool | None:
        if self._requests_session is not None:
            self._requests_session.close()
            self._requests_session = None
        if self._requests_adapter is not None:
            self._requests_adapter.close()
            self._requests_adapter = None
        # The following return statement is not needed, but it makes mypy sad without it
        return None

    # The following is needed to work around https://github.com/python/typing/issues/1992
    if TYPE_CHECKING:
        def __enter__(self) -> Self:
            return self

    @property
    def requests_session(self) -> requests.Session:
        """
        Returns the requests retry session, after initializing it if needed
        """
        if self._requests_session is None:
            self._requests_adapter = requests_retry_adapter(
                **self._requests_retry_adapter_kwargs)
            self._requests_session = requests_session(
                adapter=self._requests_adapter,
                protocol=self._requests_protocol)
        return self._requests_session


@contextmanager
def retry_session_manager(
    protocol: ProtocolType | None = None,
    **adapter_kwargs: Unpack[RequestsRetryAdapterArgs]
) -> Iterator[requests.Session]:
    """
    Provides a context manager that will clean up both the session and the adapter on exit

    If specified, protocol should omit the trailing "://" because it will be automatically appended later
    """
    requests_protocol = protocol if protocol is not None else DEFAULT_PROTOCOL
    with closing(requests_retry_adapter(**adapter_kwargs)) as adapter:
        with requests_session(adapter=adapter,
                              protocol=requests_protocol) as session:
            yield session
