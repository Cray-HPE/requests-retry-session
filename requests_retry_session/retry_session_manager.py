#
# MIT License
#
# (C) Copyright 2024 Hewlett Packard Enterprise Development LP
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

from contextlib import AbstractContextManager
# Because we want to support Python 3.6 and 3.9, use old-style type hint syntax
from typing import Optional

import requests

from .requests_retry_session import requests_retry_adapter, requests_session


class RetrySessionManager(AbstractContextManager):
    """
    Not intended to be useful on its own, this is for classes that want to create a
    retry session only when needed, and to clean it up in their __exit__ function.
    This class is not thread safe.
    """
    def __init__(self, protocol: Optional[str]=None, **requests_retry_adapter_kwargs):
        self._requests_adapter = None
        self._requests_session = None
        self._requests_protocol = protocol
        self._requests_session_kwargs = {} if protocol is None else { 'protocol': protocol }
        self._requests_retry_adapter_kwargs = requests_retry_adapter_kwargs


    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._requests_session is not None:
            self._requests_session.close()
            self._requests_adapter.close()
            self._requests_session = None
            self._requests_adapter = None

    @property
    def requests_session(self) -> requests.Session:
        if self._requests_session is None:
            self._requests_adapter = requests_retry_adapter(**self._requests_retry_adapter_kwargs)
            self._requests_session = requests_session(adapter=self._requests_adapter, **self._requests_session_kwargs)
        return self._requests_session
