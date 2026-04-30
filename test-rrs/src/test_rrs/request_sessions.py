#
# MIT License
#
# (C) Copyright 2026 Hewlett Packard Enterprise Development LP
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
Classes for managing RRS sessions
"""

from contextlib import AbstractContextManager, ExitStack
import logging
from types import TracebackType
# Because we wish to support Python versions back to 3.6, we
# import things from typing that are not necessary in newer
# Python versions
from typing import (
    List,
    Type,
    Union
)

import requests
import requests_retry_session as rrs

from .defs import ProtocolType, ReqMethodToTest

class MyRRSessionManager(rrs.RetrySessionManager):
    """
    As a subclass of RetrySessionManager, this class can be used as a context manager,
    and will have a requests session available as self.requests_session
    """
    def __init__(self, proto: ProtocolType, adapter_args: rrs.RequestsRetryAdapterArgs) -> None:
        super().__init__(protocol=proto, **adapter_args)

class RequestSessions(AbstractContextManager):
    """
    Context manager, managing three RRS sessions
    """
    def __init__(
        self,
        protocol: ProtocolType,
        adapter_args: rrs.RequestsRetryAdapterArgs
    ) -> None:
        self._proto = protocol
        self._ad_args = adapter_args
        self._non_cm_session: Union[requests.Session, None] = None
        self._cm_func_session: Union[requests.Session, None] = None
        self._cm_class_session: Union[requests.Session, None] = None
        self._stack: Union[ExitStack, None] = None

    def __enter__(self):
        # Create an ExitStack to manage multiple context managers
        self._stack = ExitStack()

        # Enter two internal context managers
        logging.debug("Creating rrs.retry_session_manager (protocol=%s args=%s)",
                      self._proto, self._ad_args)
        self._cm_func_session = self._stack.enter_context(
            rrs.retry_session_manager(protocol=self._proto, **self._ad_args)
        )
        logging.debug("Creating rrs.RetrySessionManager (protocol=%s args=%s)",
                      self._proto, self._ad_args)
        cm_class = self._stack.enter_context(
                    MyRRSessionManager(self._proto, self._ad_args)
        )
        self._cm_class_session = cm_class.requests_session
        logging.debug("Creating rrs.requests_retry_session (protocol=%s args=%s)",
                      self._proto, self._ad_args)
        self._non_cm_session = rrs.requests_retry_session(protocol=self._proto,
                                                          **self._ad_args)
        return self

    def __exit__(  # pylint: disable=useless-return
            self, exc_type: Union[Type[BaseException], None],
            exc_val: Union[BaseException, None],
            exc_tb: Union[TracebackType, None]) -> Union[bool, None]:
        # Delegate cleanup to the ExitStack
        self._cm_func_session, self._cm_class_session, self._non_cm_session = None, None, None
        return self._stack.__exit__(exc_type, exc_val, exc_tb)

    def test_list(self, method_name: str) -> List[ReqMethodToTest]:
        """
        Generate and return a list of ReqMethodToTest, based on the
        managed RRS sessions
        """
        attr_name = method_name.lower()
        method_name = method_name.upper()
        non_cm_method = getattr(self._non_cm_session, attr_name)
        non_cm_desc = f"rrs.requests_retry_session {method_name}"
        cm_func_method = getattr(self._cm_func_session, attr_name)
        cm_func_desc = f"rrs.retry_session_manager {method_name}"
        cm_class_method = getattr(self._cm_class_session, attr_name)
        cm_class_desc = f"rrs.RetrySessionManager {method_name}"
        return [
            (non_cm_method, non_cm_desc),
            (cm_func_method, cm_func_desc),
            (cm_class_method, cm_class_desc) ]
